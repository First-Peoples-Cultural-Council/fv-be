from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models import DictionaryEntry
from backend.models.characters import Character, IgnoredCharacter
from backend.models.media import Audio, Image, Video
from backend.serializers.character_serializers import (
    CharacterDetailSerializer,
    CharacterDetailWriteSerializer,
    IgnoredCharacterSerializer,
)
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of all characters available on the specified site",
        responses={
            200: CharacterDetailSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific character in the specified site",
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
        description="Edit a character in the specified site",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=CharacterDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
)
class CharactersViewSet(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, ModelViewSet
):
    """
    Character information.
    """

    http_method_names = ["get", "put"]
    serializer_class = CharacterDetailWriteSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return (
                Character.objects.filter(site__slug=site[0].slug)
                .order_by("sort_order")
                .prefetch_related("variants")
                .prefetch_related(
                    Prefetch(
                        "related_dictionary_entries",
                        queryset=DictionaryEntry.objects.visible(self.request.user),
                    ),
                    Prefetch(
                        "related_audio",
                        queryset=Audio.objects.visible(self.request.user),
                    ),
                    Prefetch(
                        "related_images",
                        queryset=Image.objects.visible(self.request.user),
                    ),
                    Prefetch(
                        "related_videos",
                        queryset=Video.objects.visible(self.request.user),
                    ),
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
            return IgnoredCharacter.objects.filter(site__slug=site[0].slug)
        else:
            return IgnoredCharacter.objects.none()
