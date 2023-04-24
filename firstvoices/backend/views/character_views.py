from itertools import groupby
from operator import itemgetter

from django.db.models.functions import Upper
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.characters import Character
from backend.models.sites import Site
from backend.predicates import utils
from backend.serializers.character_serializers import CharacterSerializer
from backend.views.base_views import FVPermissionViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of all characters the user currently has access to, organized by site.",
        responses={200: CharacterSerializer},
    ),
    retrieve=extend_schema(
        description="Details about a specific character.",
        responses={200: CharacterSerializer},
    ),
)
class CharactersViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    API endpoint that allows characters to be viewed.
    """

    http_method_names = ["get"]
    serializer_class = CharacterSerializer
    queryset = Character.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Override the list method to organize characters by site.
        """
        visible_sites = utils.filter_by_viewable(request.user, Site.objects.all())

        # Organize characters by site, then by sort order
        queryset = Character.objects.select_related("site").order_by(
            Upper("site__title"), "sort_order"
        )

        # filter by visible sites
        queryset = queryset.filter(site__in=visible_sites)

        # serialize each character (groupby can't handle Models)
        character_jsons = [
            CharacterSerializer(character, context={"request": request}).data
            for character in queryset
        ]

        # group by site
        rows = groupby(character_jsons, itemgetter("site"))
        data = [
            {
                "site": site if site is not None else "Other",
                "characters": list(items),
            }
            for site, items in rows
        ]

        return Response(data)
