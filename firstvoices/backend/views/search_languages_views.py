from django.db.models import Prefetch
from django.db.models.functions import Upper
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from elasticsearch_dsl import Search

from backend.models.sites import Language, Site, SiteFeature
from backend.serializers.site_serializers import LanguageSerializer
from backend.views import doc_strings
from backend.views.api_doc_variables import inline_site_doc_detail_serializer
from backend.views.base_views import ThrottlingMixin

from ..models.constants import Visibility
from ..search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX
from .base_search_views import BaseSearchViewSet
from .utils import get_select_related_media_fields


@extend_schema_view(
    list=extend_schema(
        description="A public list of available language sites, grouped by language. "
        "Public and member sites are included, as well as any team sites the user has access to. If there "
        "are no accessible sites the list will be empty. Sites with no specified language will be grouped "
        "under 'More FirstVoices Sites'.",
        responses={200: LanguageSerializer},
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
    serializer_class = LanguageSerializer
    model = Language

    def build_query(self, **kwargs):
        """Subclasses should implement.

        Returns: elasticsearch_dsl.search.Search object specifying the query to execute
        """
        return Search(index=ELASTICSEARCH_LANGUAGE_INDEX)

    def make_queryset_eager(self, model_name, queryset):
        """Subclasses can implement this to add prefetching, etc"""
        # prefetch via the serializer
        visible_sites = Site.objects.filter(visibility__gte=Visibility.MEMBERS)
        return LanguageSerializer.make_queryset_eager(
            queryset, visible_sites=visible_sites
        )

    def serialize_search_results(self, search_results, data):
        languages = {str(d.id): d for d in data["Language"]}
        return [
            LanguageSerializer(
                languages[result["_source"]["document_id"]],
                context={"request": self.request},
            ).data
            for result in search_results
        ]

        # todo: "other sites"

    def get_detail_queryset(self):
        return (
            Language.objects.all()
            .order_by(Upper("title"))
            .prefetch_related(
                Prefetch(
                    "sites",
                    queryset=Site.objects.visible(user=self.request.user)
                    .order_by(Upper("title"))
                    .select_related(*get_select_related_media_fields("logo")),
                ),
                Prefetch(
                    "sites__sitefeature_set",
                    queryset=SiteFeature.objects.filter(is_enabled=True),
                ),
            )
        )

    #
    # def list(self, request, *args, **kwargs):
    #     """
    #     Return a list of sites grouped by language.
    #     """
    #     # create the search query
    #
    #     # execute the search
    #
    #     # hydrate the data
    #
    #     # serialize the results

    #
    #     # retrieve visible sites in order to filter out empty languages
    #     sites = Site.objects.filter(visibility__gte=Visibility.MEMBERS)
    #     ids_of_languages_with_sites = sites.values_list("language_id", flat=True)
    #
    #     # then retrieve the desired data as a Language queryset
    #     # sorting note: titles are converted to uppercase and then sorted which will put custom characters at the end
    #     languages = (
    #         Language.objects.filter(id__in=ids_of_languages_with_sites)
    #         .order_by(Upper("title"))
    #         .prefetch_related(
    #             Prefetch(
    #                 "sites",
    #                 queryset=sites.order_by(Upper("title")).select_related(
    #                     *get_select_related_media_fields("logo")
    #                 ),
    #             ),
    #             Prefetch(
    #                 "sites__sitefeature_set",
    #                 queryset=SiteFeature.objects.filter(is_enabled=True),
    #             ),
    #         )
    #     )
    # #
    #     data = [
    #         LanguageSerializer(language, context={"request": request}).data
    #         for language in languages
    #     ]
    #
    #     # add "other" sites
    #     other_sites = (
    #         sites.filter(language=None)
    #         .order_by(Upper("title"))
    #         .select_related(*get_select_related_media_fields("logo"))
    #         .prefetch_related(
    #             Prefetch(
    #                 "sitefeature_set",
    #                 queryset=SiteFeature.objects.filter(is_enabled=True),
    #             ),
    #         )
    #     )
    #
    #     if other_sites:
    #         other_site_json = {
    #             "language": "More FirstVoices Sites",
    #             "languageCode": "",
    #             "sites": [
    #                 SiteSummarySerializer(site, context={"request": request}).data
    #                 for site in other_sites
    #             ],
    #         }
    #
    #         data.append(other_site_json)
    #
    #     return Response(data)
