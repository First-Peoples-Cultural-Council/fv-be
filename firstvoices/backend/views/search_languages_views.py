from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from elasticsearch_dsl import Q, Search

from backend.models.sites import Language, Site
from backend.search.queries.text_matching import (
    exact_match,
    fuzzy_match,
    substring_match,
)
from backend.search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX
from backend.serializers.language_serializers import (
    LanguagePlaceholderSerializer,
    LanguageSerializer,
)
from backend.views import doc_strings
from backend.views.api_doc_variables import inline_site_doc_detail_serializer
from backend.views.base_views import ThrottlingMixin

from ..serializers.site_serializers import SiteSummarySerializer
from .base_search_views import BaseSearchViewSet

PRIMARY_BOOST = 5
SECONDARY_BOOST = 3


@extend_schema_view(
    list=extend_schema(
        description="A list of available language sites, grouped by language. "
        "Public and member sites are included. If there "
        "are no accessible sites the list will be empty. Sites with no specified language will be grouped "
        "under 'More FirstVoices Sites'.",
        responses={200: LanguageSerializer},
        parameters=[
            OpenApiParameter(
                name="q",
                description="Search term. May be a language code (BCP-47 / ISO), name or alternate name of a "
                "language or language family, community keyword, or site title.",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample("language code", value="en"),
                    OpenApiExample("language name", value="Esperanto"),
                    OpenApiExample("community keyword", value="Example First Nation"),
                    OpenApiExample("site title", value="public demo site"),
                ],
            )
        ],
    ),
    retrieve=extend_schema(
        description="Basic information about a language.",
        responses={
            200: inline_site_doc_detail_serializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
)
class LanguageViewSet(ThrottlingMixin, BaseSearchViewSet):
    """
    Summary information about languages.
    """

    http_method_names = ["get"]
    serializer_classes = {
        "Language": LanguageSerializer,
        "Site": LanguagePlaceholderSerializer,
    }
    model = Language

    def build_query(self, q, **kwargs):
        """
        Returns: elasticsearch_dsl.search.Search object specifying the query to execute
        """
        if q:
            return self.build_search_term_query(q)

        else:
            return self.build_list_query()

    def build_search_term_query(self, q):
        """
        Search results are ranked as follows:
        * exact match on a canonical or visible value (language code, language title, site title, language family title)
        * exact match on an alternate or hidden value (alternate spellings, alternate names, community names)
        * fuzzy match on any search field except language code

        Args:
            q: search term

        Returns: ElasticSearch query object

        """
        subqueries = [
            exact_match(q, field="language_code", boost=PRIMARY_BOOST),
            exact_match(q, field="primary_search_fields", boost=PRIMARY_BOOST),
            exact_match(q, field="secondary_search_fields", boost=SECONDARY_BOOST),
            fuzzy_match(q, field="primary_search_fields"),
            fuzzy_match(q, field="secondary_search_fields"),
            substring_match(q, field="primary_search_fields"),
            substring_match(q, field="secondary_search_fields"),
        ]
        return Search(index=ELASTICSEARCH_LANGUAGE_INDEX).query(
            Q(
                "bool",
                should=subqueries,
                minimum_should_match=1,
            )
        )

    def build_list_query(self):
        return (
            Search(index=ELASTICSEARCH_LANGUAGE_INDEX)
            .query(Q("bool", filter=[Q("term", document_type="Language")]))
            .sort({"sort_title": {"order": "asc"}})
        )

    def make_queryset_eager(self, model_name, queryset):
        if model_name == "Language":
            visible_sites = Site.objects.explorable()
            return LanguageSerializer.make_queryset_eager(
                queryset, visible_sites=visible_sites
            )

        if model_name == "Site":
            return LanguagePlaceholderSerializer.make_queryset_eager(queryset)

        return super().make_queryset_eager(model_name, queryset)

    def serialize_search_results(self, search_results, data, **kwargs):
        serialized_data = super().serialize_search_results(
            search_results, data, **kwargs
        )

        if not kwargs["q"]:
            # add "More FirstVoices Sites" section at the end of list results
            other_sites_json = self.get_other_sites_data()
            if other_sites_json:
                serialized_data.append(other_sites_json)

        return serialized_data

    def get_other_sites_data(self):
        other_sites = Site.objects.explorable().filter(language=None)

        if other_sites:
            queryset = LanguagePlaceholderSerializer.make_queryset_eager(other_sites)

            other_sites_json = LanguagePlaceholderSerializer(
                queryset.first(), context=self.get_serializer_context()
            ).data
            other_sites_json["sites"] = SiteSummarySerializer(
                queryset, many=True, context=self.get_serializer_context()
            ).data
            return other_sites_json

        return None
