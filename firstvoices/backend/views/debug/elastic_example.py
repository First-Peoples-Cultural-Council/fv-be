from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from firstvoices.settings import ELASTICSEARCH_HOST, ELASTICSEARCH_PRIMARY_INDEX


class ExampleElasticSearch(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        es = Elasticsearch(hosts=ELASTICSEARCH_HOST)

        # this is just a hack to make sure there's something in there. really your indexing will happen elsewhere
        es.index(
            index=ELASTICSEARCH_PRIMARY_INDEX,
            document={"title": "spam", "category": "breakfast"},
        )

        es.index(
            index=ELASTICSEARCH_PRIMARY_INDEX,
            document={"title": "spam", "category": "email"},
        )

        es.index(
            index=ELASTICSEARCH_PRIMARY_INDEX,
            document={"title": "eggs", "category": "breakfast"},
        )

        s = (
            Search(using=es, index="fv")
            .filter("term", category="breakfast")
            .query("fuzzy", title="spaam")
        )
        elastic_says = s.execute()

        return Response(
            {
                "hits": map(
                    lambda h: {
                        "score": h.meta.score,
                        "title": h.title,
                        "id": h.meta.id,
                    },
                    elastic_says,
                )
            },
            status=200,
        )
