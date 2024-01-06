from django.db.models.expressions import RawSQL
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.models import Character, DictionaryEntry
from backend.views.base_views import SiteContentViewSetMixin

SOLUTION_LENGTH = 5


class WordsyViewSet(SiteContentViewSetMixin, GenericViewSet):
    http_method_names = ["get"]
    pagination_class = None
    queryset = ""

    def list(self, request, **kwargs):
        site = self.get_validated_site()[0]

        orthography = (
            Character.objects.filter(site=site)
            .order_by("sort_order")
            .values_list("title", flat=True)
        )
        words = (
            DictionaryEntry.objects.annotate(
                chars_length=RawSQL(
                    "ARRAY_LENGTH(ARRAY_REMOVE(split_chars_base, ' '), 1)", ()
                )
            )
            .filter(
                site=site,
                visibility=site.visibility,
                exclude_from_games=False,
                exclude_from_kids=False,
                chars_length__exact=SOLUTION_LENGTH,
            )
            .order_by("custom_order")
            .values_list("title", flat=True)
        )
        valid_guesses = words
        solution = ""

        return Response(
            data={
                "orthography": orthography,
                "words": words,
                "valid_guesses": valid_guesses,
                "solution": solution,
            }
        )
