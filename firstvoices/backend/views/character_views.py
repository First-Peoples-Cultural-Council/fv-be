from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models import DictionaryEntry
from backend.models.characters import Character, IgnoredCharacter
from backend.serializers.character_serializers import (
    CharacterDetailSerializer,
    IgnoredCharacterSerializer,
)
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from backend.views.utils import get_media_prefetch_list


@extend_schema_view(
    list=extend_schema(
        description="A list of all characters available on the specified site.",
        responses={
            200: CharacterDetailSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific character in the specified site.",
        responses={
            200: CharacterDetailSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    update=extend_schema(
        description="Edit a character in the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=CharacterDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    partial_update=extend_schema(
        description="Edit a character in the specified site. Any omitted fields will be unchanged.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=CharacterDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class CharactersViewSet(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, ModelViewSet
):
    """
    Character information.
    """

    http_method_names = ["get", "put", "patch"]
    serializer_class = CharacterDetailSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            media_prefetches = get_media_prefetch_list(self.request.user)
            return (
                Character.objects.filter(site__slug=site[0].slug)
                .order_by("sort_order")
                .select_related(
                    "site", "site__language", "created_by", "last_modified_by"
                )
                .prefetch_related(
                    "variants",
                    *media_prefetches,
                    Prefetch(
                        "related_dictionary_entries",
                        queryset=DictionaryEntry.objects.visible(self.request.user)
                        .select_related("site")
                        .prefetch_related(*media_prefetches, "translation_set"),
                    )
                )
            )
        else:
            return Character.objects.none()


@extend_schema_view(
    list=extend_schema(
        description="A list of all ignored characters on the specified site",
        responses={
            200: IgnoredCharacterSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about an ignored character in the specified site",
        responses={
            200: IgnoredCharacterSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class IgnoredCharactersViewSet(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, ModelViewSet
):
    """
    Information about ignored characters.
    """

    http_method_names = ["get"]
    serializer_class = IgnoredCharacterSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return IgnoredCharacter.objects.filter(
                site__slug=site[0].slug
            ).select_related("site", "site__language", "created_by", "last_modified_by")
        else:
            return IgnoredCharacter.objects.none()
