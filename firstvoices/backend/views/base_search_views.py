import logging

from rest_framework import viewsets
from rest_framework.response import Response

from backend import models
from backend.pagination import SearchPageNumberPagination
from backend.search.queries.query_builder import get_base_paginate_query
from backend.search.utils import (
    get_base_search_params,
    get_ids_by_type,
    get_search_response,
)


def queryset_as_map(queryset):
    return {str(x.id): x for x in queryset}


class HydrateSerializeSearchResultsMixin:
    serializer_classes = {}

    def get_serializer_class_for_model_type(self, model_type):
        if model_type in self.serializer_classes:
            return self.serializer_classes[model_type]

        return self.serializer_class

    def serialize_search_results(self, search_results, data, **kwargs):
        """
        Serializes the given search results, using the provided data and the configured serializer classes.

        Params:
            search_results: a list of ElasticSearch hits
            data: a dictionary of data objects keyed by model, as returned by the hydrate method

        Returns: a list of serializer data in the order of the given search_results.
        """
        serialized_data = []

        for result in search_results:
            item = self.serialize_result(result, data)
            if item:
                serialized_data.append(item)

        return serialized_data

    def serialize_result(self, result, data):
        """Serializes a single search_result, using the provided hydration data and the configured serializer classes.

        Params:
            search_result: an ElasticSearch hit
            data: a dictionary of data objects keyed by model, as returned by the hydrate method

        Returns: serializer data
        """

        data_to_serialize = self.get_data_to_serialize(result, data)

        if not data_to_serialize:
            return None

        result_type = result["_source"]["document_type"]
        serializer = self.get_serializer_class_for_model_type(result_type)
        context = self.get_serializer_context()

        return serializer(data_to_serialize, context=context).data

    def get_data_to_serialize(self, result, data):
        result_type = result["_source"]["document_type"]
        result_id = result["_source"]["document_id"]
        try:
            return data[str(result_type)][str(result_id)]
        except KeyError:
            logger = logging.getLogger(__name__)
            logger.warning(
                "Search result was not found in database. [%s] id [%s]",
                result_type,
                result_id,
            )

        return None

    def hydrate(self, search_results):
        """Retrieves data for each item in the search results, grouped by type. If a serializer is defined for the type,
        attempts to use the serializer to add eager fetching (prefetch, etc). Returns actual data not lazy querysets.

            Returns: a dictionary where the keys are model names and the values are maps of { model_id: model_instance}
                for that type.
        """
        ids = get_ids_by_type(search_results)
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
        serializer = self.get_serializer_class_for_model_type(model_name)
        if hasattr(serializer, "make_queryset_eager"):
            return serializer.make_queryset_eager(queryset)
        else:
            return queryset

    def hydrate_and_serialize_search_results(
        self, search_results, search_params, pagination_params
    ):
        data = self.hydrate(search_results)
        return self.serialize_search_results(
            search_results, data, **search_params, **pagination_params
        )


class BaseSearchViewSet(viewsets.GenericViewSet, HydrateSerializeSearchResultsMixin):
    http_method_names = ["get"]
    pagination_class = SearchPageNumberPagination
    queryset = ""

    def get_search_params(self):
        return get_base_search_params(self.request)

    def has_invalid_input(self, search_params):
        """Subclasses can override to define cases where response should be an empty list."""
        return False

    def build_query(self, **kwargs):
        """Subclasses should implement.

        Returns: elasticsearch.dsl.search.Search object specifying the query to execute
        """
        raise NotImplementedError()

    def paginate_query(self, search_query, **kwargs):
        return get_base_paginate_query(search_query, **kwargs)

    def sort_query(self, search_query, **kwargs):
        """Subclasses can implement to add sort parameters."""
        return search_query

    def get_search_query(self, search_params, pagination_params):
        search_query = self.build_query(**search_params)
        search_query = self.paginate_query(search_query, **pagination_params)
        return self.sort_query(search_query, **search_params)

    def list(self, request, **kwargs):
        search_params = self.get_search_params()
        pagination_params = self.get_pagination_params()

        if self.has_invalid_input(search_params):
            return self.paginate_search_response(request, [], 0)

        search_query = self.get_search_query(search_params, pagination_params)

        response = get_search_response(search_query)
        search_results = response["hits"]["hits"]
        serialized_data = self.hydrate_and_serialize_search_results(
            search_results, search_params, pagination_params
        )

        return self.paginate_search_response(
            request, serialized_data, response["hits"]["total"]["value"]
        )

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

    def paginate_search_response(self, request, serialized_data, result_count):
        page = self.paginator.apply_search_pagination(
            request=request,
            object_list=serialized_data,
            count=result_count,
        )
        if page is not None:
            return self.get_paginated_response(page)

        return Response(data=serialized_data)
