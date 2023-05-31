from elasticsearch.exceptions import ConnectionError
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from backend.search.query_builder import get_search_query
from backend.search.utils.object_utils import hydrate_objects
from backend.views.exceptions import ElasticSearchConnectionError


class CustomSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ["get"]
    queryset = ""

    def get_search_params(self):
        """
        Function to return search params in a structured format.
        """
        input_q = self.request.GET.get("q", "")

        return {"q": input_q}

    def list(self, request):
        # Raise 500 if elasticsearch is not running, or return an empty list ?

        search_params = self.get_search_params()

        # Get search query
        search_query = get_search_query(q=search_params["q"])

        # Get search results
        try:
            response = search_query.execute()
        except ConnectionError:
            raise ElasticSearchConnectionError()

        search_results = response["hits"]["hits"]

        # Adding data to objects
        hydrated_objects = hydrate_objects(search_results, request)

        # view permissions and pagination to be applied

        # Structuring response
        return Response(data=hydrated_objects)
