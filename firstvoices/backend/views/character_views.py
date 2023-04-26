from django.core.exceptions import PermissionDenied
from django.http import Http404
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models.characters import Character
from backend.models.sites import Site
from backend.predicates import utils
from backend.serializers.character_serializers import CharacterDetailSerializer
from backend.views.base_views import FVPermissionViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of all characters available on the specified site",
        # TODO add site ignored characters to this list
        responses={
            200: CharacterDetailSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
    retrieve=extend_schema(
        description="Details about a specific character in the specified site",
        # TODO add character variants to the detail view
        responses={
            200: CharacterDetailSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
)
class CharactersViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    Character information.
    """

    http_method_names = ["get"]
    serializer_class = CharacterDetailSerializer

    def get_validated_site(self):
        site_slug = self.kwargs["site_slug"]
        site = Site.objects.filter(slug=site_slug)

        if site.count() == 0:
            raise Http404

        if utils.filter_by_viewable(self.request.user, site).count() == 0:
            raise PermissionDenied

        return site

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return Character.objects.filter(site__slug=site[0].slug).order_by(
                "sort_order"
            )
        else:
            return Character.objects.filter(site__slug=None)
