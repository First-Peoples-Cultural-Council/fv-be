from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from backend.models.dictionary import TypeOfDictionaryEntry
from backend.search_indexes.dictionary_documents import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
)
from backend.serializers.dictionary_serializers import DictionaryEntrySummarySerializer
from backend.views.search.utils import hydrate_objects


class CustomSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ["get"]
    serializer_class = DictionaryEntrySummarySerializer
    queryset = ""

    @staticmethod
    def get_elasticsearch_client():
        list_of_indices = [ELASTICSEARCH_DICTIONARY_ENTRY_INDEX]
        client = Elasticsearch()
        s = Search(using=client, index=list_of_indices)
        return s

    def get_search_params(self):
        q = self.request.GET.get("q", "")
        doc_types = self.request.GET.get("docType", "")
        if len(doc_types):
            doc_types = doc_types.split("|")
        else:
            doc_types = TypeOfDictionaryEntry.values

        return {"q": q, "doc_types": doc_types}

    def get_raw_objects(self):
        s = self.get_elasticsearch_client()
        search_params = self.get_search_params()
        search_query = s.query("match", title=search_params["q"])

        # Check if both word and phrase are in doc_types, else we will have to filter one out
        if (
            "WORD" in search_params["doc_types"]
            and "PHRASE" not in search_params["doc_types"]
        ):
            search_query = search_query.exclude(
                "term", dictionary_entry__type=TypeOfDictionaryEntry.PHRASE
            )
        elif (
            "PHRASE" in search_params["doc_types"]
            and "WORD" not in search_params["doc_types"]
        ):
            search_query = search_query.exclude(
                "term", dictionary_entry__type=TypeOfDictionaryEntry.WORD
            )

        response = search_query.execute()
        if response["hits"]["total"]["value"]:
            raw_objects = []
            for hit in response["hits"]["hits"]:
                raw_objects.append(hit)
        return raw_objects

    def list(self, request):
        raw_objects = self.get_raw_objects()

        # Adding data to objects
        hydrated_objects = hydrate_objects(raw_objects)

        # todo: Apply view permissions

        # todo: Apply pagination

        # Structuring response
        return Response(data=hydrated_objects)
