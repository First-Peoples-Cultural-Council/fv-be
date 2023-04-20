from itertools import groupby
from operator import itemgetter

from django.db.models.functions import Upper
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from firstvoices.backend.models.characters import (
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from firstvoices.backend.models.sites import Site
from firstvoices.backend.predicates import utils
from firstvoices.backend.serializers.character_serializers import (
    CharacterSerializer,
    CharacterVariantSerializer,
    IgnoredCharacterSerializer,
)
from firstvoices.backend.views.base_views import FVPermissionViewSetMixin


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


@extend_schema_view(
    list=extend_schema(
        description="A list of all character variants the user currently has access to, organized by site.",
        responses={200: CharacterVariantSerializer},
    ),
    retrieve=extend_schema(
        description="Details about a specific character.",
        responses={200: CharacterVariantSerializer},
    ),
)
class CharacterVariantsViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    API endpoint that allows character variants to be viewed.
    """

    http_method_names = ["get"]
    serializer_class = CharacterVariantSerializer
    queryset = CharacterVariant.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Override the list method to organize character variants by site.
        """
        visible_sites = utils.filter_by_viewable(request.user, Site.objects.all())

        # Organize character variants by site, then by sort order
        queryset = CharacterVariant.objects.select_related("site").order_by(
            Upper("site__title"), "base_character__sort_order"
        )

        # filter by visible sites
        queryset = queryset.filter(site__in=visible_sites)

        # serialize each character variant (groupby can't handle Models)
        character_variant_jsons = [
            CharacterVariantSerializer(
                character_variant, context={"request": request}
            ).data
            for character_variant in queryset
        ]

        # group by site
        rows = groupby(character_variant_jsons, itemgetter("site"))
        data = [
            {
                "site": site if site is not None else "Other",
                "character_variants": list(items),
            }
            for site, items in rows
        ]

        return Response(data)


@extend_schema_view(
    list=extend_schema(
        description="A list of all ignored characters the user currently has access to, organized by site.",
        responses={200: CharacterVariantSerializer},
    ),
    retrieve=extend_schema(
        description="Details about a specific ignored character.",
        responses={200: CharacterVariantSerializer},
    ),
)
class IgnoredCharactersViewSet(FVPermissionViewSetMixin, ModelViewSet):
    """
    API endpoint that allows ignored characters to be viewed.
    """

    http_method_names = ["get"]
    serializer_class = IgnoredCharacterSerializer
    queryset = IgnoredCharacter.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Override the list method to organize ignored characters by site.
        """
        visible_sites = utils.filter_by_viewable(request.user, Site.objects.all())

        # Organize ignored characters by site, then by title
        queryset = IgnoredCharacter.objects.select_related("site").order_by(
            Upper("site__title"), "title"
        )

        # filter by visible sites
        queryset = queryset.filter(site__in=visible_sites)

        # serialize each ignored character (groupby can't handle Models)
        ignored_character_jsons = [
            IgnoredCharacterSerializer(
                ignored_character, context={"request": request}
            ).data
            for ignored_character in queryset
        ]

        # group by site
        rows = groupby(ignored_character_jsons, itemgetter("site"))
        data = [
            {
                "site": site if site is not None else "Other",
                "ignored_characters": list(items),
            }
            for site, items in rows
        ]

        return Response(data)
