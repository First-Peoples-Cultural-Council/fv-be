import math

from django.db.models.expressions import RawSQL
from django.utils.timezone import datetime
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.models import Character, DictionaryEntry
from backend.views.base_views import SiteContentViewSetMixin

SOLUTION_LENGTH = 5


def get_wordsy_solution_seed(num_words):
    # inspired from previous fv-wordsy game with slight modification
    epoch = datetime(2024, 1, 1, 0, 0, 0).timestamp()  # wordsy game epoch
    now = datetime.now().timestamp()
    seconds_in_day = 86400
    index = math.floor((now - epoch) / seconds_in_day)
    return index % num_words


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
        words = list(
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
        if len(words):
            seed = get_wordsy_solution_seed(len(words))
            solution = words[seed]

        return Response(
            data={
                "orthography": orthography,
                "words": words,
                "valid_guesses": valid_guesses,
                "solution": solution,
            }
        )
