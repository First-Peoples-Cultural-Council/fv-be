from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets

from backend.models import Alphabet, Character, CharacterVariant, IgnoredCharacter
from backend.models.dictionary import DictionaryEntry
from backend.serializers.dictionary_serializers import DictionaryEntryDetailSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of available dictionary entries for the specified site.",
        responses={
            200: DictionaryEntryDetailSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
    retrieve=extend_schema(
        description="A dictionary entry from the specified site.",
        responses={
            200: DictionaryEntryDetailSerializer,
            403: OpenApiResponse(description="Todo: Error Not Authorized"),
            404: OpenApiResponse(description="Todo: Not Found"),
        },
    ),
)
class DictionaryViewSet(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, viewsets.ModelViewSet
):
    """
    Dictionary entry information.
    """

    http_method_names = ["get"]
    serializer_class = DictionaryEntryDetailSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        if len(site) > 0:
            return (
                DictionaryEntry.objects.filter(site__slug=site[0].slug)
                .select_related("site")
                .prefetch_related(
                    "acknowledgement_set",
                    "alternatespelling_set",
                    "note_set",
                    "pronunciation_set",
                    "translation_set",
                    "translation_set__part_of_speech",
                    "categories",
                    Prefetch(
                        "related_dictionary_entries",
                        queryset=DictionaryEntry.objects.visible(self.request.user),
                    ),
                )
            )
        else:
            return DictionaryEntry.objects.none()

    def get_serializer_context(self):
        """
        A helper function to gather additional model context which can be reused for multiple dictionary entries.
        """

        site = self.get_validated_site()[0]

        context = super().get_serializer_context()

        alphabet = Alphabet.objects.filter(site=site).first()
        ignored_characters = IgnoredCharacter.objects.filter(site=site).values_list(
            "title", flat=True
        )
        base_characters = Character.objects.filter(site=site).order_by("sort_order")
        character_variants = CharacterVariant.objects.filter(site=site)
        ignorable_characters = IgnoredCharacter.objects.filter(site=site)

        context["alphabet"] = alphabet
        context["ignored_characters"] = ignored_characters
        context["base_characters"] = base_characters
        context["character_variants"] = character_variants
        context["ignorable_characters"] = ignorable_characters
        return context
