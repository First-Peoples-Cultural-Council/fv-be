from elasticsearch.exceptions import ConnectionError
from rest_framework import viewsets
from rest_framework.response import Response

from backend import models
from backend.pagination import SearchPageNumberPagination
from backend.views.exceptions import ElasticSearchConnectionError


class BaseSearchViewSet(viewsets.GenericViewSet):
    http_method_names = ["get"]
    queryset = ""
    pagination_class = SearchPageNumberPagination
    serializer_classes = {}

    def get_search_params(self):
        """
        Returns validated search parameters based on request inputs.
        """
        return {
            "q": self.request.GET.get("q", ""),  # todo: validate and clean,
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

        search_query = self.build_query(**search_params, **pagination_params)

        try:
            response = search_query.execute()
        except ConnectionError:
            raise ElasticSearchConnectionError()

        search_results = response["hits"]["hits"]
        data = self.hydrate(search_results)
        serialized_data = self.serialize_search_results(search_results, data)
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

    def hydrate(self, search_results):
        """Constructs querysets for each type of model in the search results. If a serializer is defined for the type,
        we attempt to use the serializer to add eager fetching (prefetch, etc).

            Returns: a dictionary where the keys are model names and the values are querysets
        """
        ids = self.get_ids_by_type(search_results)
        querysets = {}

        for model_name, model_ids in ids.items():
            queryset = getattr(models, model_name).objects.filter(id__in=model_ids)
            queryset = self.make_queryset_eager(model_name, queryset)

            querysets[model_name] = queryset

        return querysets

    def make_queryset_eager(self, model_name, queryset):
        """Subclasses can implement this to add prefetching, etc"""
        return queryset

    def get_ids_by_type(self, search_results):
        """Organizes model IDs of the search results by data type.

        Returns: a dictionary where the keys are model names and the values are lists of ids
        """
        data = {}
        for result in search_results:
            model_name = result["_source"]["document_type"]  # todo get name not class
            model_id = result["_source"]["document_id"]

            if model_name not in data:
                data[model_name] = []

            data[model_name].append(model_id)
        return data

    def serialize_search_results(self, search_results, data):
        """Subclasses should implement.

        Params:
            search_results: a list of ElasticSearch hits
            data: a dictionary of data objects keyed by model, as returned by the hydrate method

        Returns: a list of serializer data.
        """
        raise NotImplementedError()
