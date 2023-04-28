from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models.characters import Character, IgnoredCharacter
from backend.serializers.character_serializers import (
    CharacterDetailSerializer,
    IgnoredCharacterSerializer,
)
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of all characters available on the specified site",
        responses={
            200: CharacterDetailSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
    retrieve=extend_schema(
        description="Details about a specific character in the specified site",
        responses={
            200: CharacterDetailSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
)
class CharactersViewSet(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, ModelViewSet
):
    """
    Character information.
    """

    http_method_names = ["get"]
    serializer_class = CharacterDetailSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return (
                Character.objects.filter(site__slug=site[0].slug)
                .order_by("sort_order")
                .prefetch_related("variants")
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
    ),
    retrieve=extend_schema(
        description="Details about an ignored character in the specified site",
        responses={
            200: IgnoredCharacterSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
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
