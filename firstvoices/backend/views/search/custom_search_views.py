from rest_framework import mixins, viewsets
from rest_framework.response import Response

from backend.search.query_builder import get_search_query
from backend.search.utils.object_utils import hydrate_objects


class CustomSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ["get"]
    queryset = ""

    def get_search_params(self):
        """
        Function to return search params in a structured format.
        """
        input_q = self.request.GET.get("q", "")

        return {"q": input_q}

    def get_raw_objects(self):
        """
        Function to build and execute the search query.
        Returns raw objects returned from elastic-search.
        """
        search_params = self.get_search_params()
        search_query = get_search_query(q=search_params["q"])
        raw_objects = []
        response = search_query.execute()
        if response["hits"]["total"]["value"]:
            for hit in response["hits"]["hits"]:
                raw_objects.append(hit)
        return raw_objects

    def list(self, request):
        # Raise 500 if elasticsearch is not running, or return an empty list ?

        raw_objects = self.get_raw_objects()

        # Adding data to objects
        hydrated_objects = hydrate_objects(raw_objects)

        # view permissions and pagination to be applied

        # Structuring response
        return Response(data=hydrated_objects)
