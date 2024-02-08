from elasticsearch.exceptions import ConnectionError
from rest_framework import viewsets
from rest_framework.response import Response

from backend import models
from backend.pagination import SearchPageNumberPagination
from backend.utils.character_utils import clean_input
from backend.views.exceptions import ElasticSearchConnectionError


def queryset_as_map(queryset):
    return {str(x.id): x for x in queryset}


class BaseSearchViewSet(viewsets.GenericViewSet):
    http_method_names = ["get"]
    queryset = ""
    pagination_class = SearchPageNumberPagination
    serializer_classes = {}

    def get_search_params(self):
        """
        Returns validated search parameters based on request inputs.
        """
        cleaned_q = clean_input(self.request.GET.get("q", ""))

        return {
            "q": cleaned_q.lower(),
            "user": self.request.user,
        }

    def get_pagination_params(self):
        """
        Returns pagination parameters.
        """
        default_page_size = self.paginator.get_page_size(self.request)

        page = self.paginator.override_invalid_number(self.request.GET.get("page", 1))

        page_size = self.paginator.override_invalid_number(
            self.request.GET.get("pageSize", default_page_size), default_page_size
        )

        start = (page - 1) * page_size

        return {
            "page_size": page_size,
            "page": page,
            "start": start,
        }

    def get_serializer_class(self, model_type):
        if model_type in self.serializer_classes:
            return self.serializer_classes[model_type]

        return self.serializer_class

    def list(self, request, **kwargs):
        search_params = self.get_search_params()
        pagination_params = self.get_pagination_params()

        search_query = self.build_query(**search_params)
        search_query = self.paginate_query(search_query, **pagination_params)

        try:
            response = search_query.execute()
        except ConnectionError:
            raise ElasticSearchConnectionError()

        search_results = response["hits"]["hits"]
        data = self.hydrate(search_results)
        serialized_data = self.serialize_search_results(
            search_results, data, **search_params, **pagination_params
        )
        page = self.paginator.apply_search_pagination(
            request=request,
            object_list=serialized_data,
            count=response["hits"]["total"]["value"],
        )

        if page is not None:
            return self.get_paginated_response(page)

        return Response(data=serialized_data)

    def build_query(self, **kwargs):
        """Subclasses should implement.

        Returns: elasticsearch_dsl.search.Search object specifying the query to execute
        """
        raise NotImplementedError()

    def paginate_query(self, search_query, **kwargs):
        return search_query.extra(from_=kwargs["start"], size=kwargs["page_size"])

    def hydrate(self, search_results):
        """Retrieves data for each item in the search results, grouped by type. If a serializer is defined for the type,
        attempts to use the serializer to add eager fetching (prefetch, etc). Returns actual data not lazy querysets.

            Returns: a dictionary where the keys are model names and the values are maps of { model_id: model_instance}
                for that type.
        """
        ids = self.get_ids_by_type(search_results)
        data = {}

        for model_name, model_ids in ids.items():
            queryset = getattr(models, model_name).objects.filter(id__in=model_ids)
            queryset = self.make_queryset_eager(model_name, queryset)

            data[model_name] = queryset_as_map(queryset)

        return data

    def make_queryset_eager(self, model_name, queryset):
        """Attempts to add eager fetching (select related, prefetch, etc) to the provided queryset, based on the
        configured serializer class for the provided type.

        Subclasses can override this to add custom prefetching.

        Returns: updated queryset
        """
        serializer = self.get_serializer_class(model_name)
        if hasattr(serializer, "make_queryset_eager"):
            return serializer.make_queryset_eager(queryset)
        else:
            return queryset

    def get_ids_by_type(self, search_results):
        """Organizes model IDs of the search results by data type.

        Returns: a dictionary where the keys are model names and the values are lists of ids
        """
        data = {}
        for result in search_results:
            model_name = result["_source"]["document_type"]
            model_id = result["_source"]["document_id"]

            if model_name not in data:
                data[model_name] = []

            data[model_name].append(model_id)
        return data

    def serialize_search_results(self, search_results, data, **kwargs):
        """
        Serializes the given search results, using the provided data and the configured serializer classes.

        Params:
            search_results: a list of ElasticSearch hits
            data: a dictionary of data objects keyed by model, as returned by the hydrate method

        Returns: a list of serializer data in the order of the given search_results.
        """
        return [self.serialize_result(result, data) for result in search_results]

    def serialize_result(self, result, data):
        """Serializes a single search_result, using the provided hydration data and the configured serializer classes.

        Params:
            search_result: an ElasticSearch hit
            data: a dictionary of data objects keyed by model, as returned by the hydrate method

        Returns: serializer data
        """

        result_type = result["_source"]["document_type"]
        result_id = result["_source"]["document_id"]
        model = data[result_type][result_id]
        serializer = self.get_serializer_class(result_type)
        context = self.get_serializer_context()

        return serializer(model, context=context).data
