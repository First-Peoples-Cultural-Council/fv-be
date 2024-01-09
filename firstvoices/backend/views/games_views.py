import math

from django.core.cache import caches
from django.db.models.expressions import RawSQL
from django.utils.timezone import datetime
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.models import Character, DictionaryEntry
from backend.views.base_views import SiteContentViewSetMixin

CACHE_KEY_WORDSY = "wordsy"
SOLUTION_LENGTH = 5


def get_wordsy_solution_seed(num_words):
    # inspired from previous fv-wordsy game
    epoch = datetime(2024, 1, 1, 0, 0, 0).timestamp()  # wordsy game epoch
    now = datetime.now().timestamp()
    seconds_in_day = 86400000
    index = math.floor((now - epoch) / seconds_in_day)
    return index % num_words


class WordsyViewSet(SiteContentViewSetMixin, GenericViewSet):
    http_method_names = ["get"]
    pagination_class = None
    queryset = ""

    def list(self, request, **kwargs):
        site = self.get_validated_site()[0]

        # setting cache_expiry to 23:59 for current date
        today = datetime.today().date()
        eod = datetime.today().time().max
        cache_expiry = (
            datetime.combine(today, eod)
            - datetime.combine(today, datetime.now().time())
        ).total_seconds()

        # Checking if required query sets are present in cache
        cache_key_orthography = f"{site.title}-orthography"
        cache_key_words = f"{site.title}-words"

        # orthography
        orthography_qs = caches[CACHE_KEY_WORDSY].get(cache_key_orthography)
        if orthography_qs is None:
            orthography_qs = list(
                Character.objects.filter(site=site)
                .order_by("sort_order")
                .values_list("title", flat=True)
            )
            caches[CACHE_KEY_WORDSY].set(
                cache_key_orthography, orthography_qs, cache_expiry
            )

        # words
        words_qs = caches[CACHE_KEY_WORDSY].get(cache_key_words)
        if words_qs is None:
            # Filtering words based on their length excluding spaces
            words_qs = list(
                DictionaryEntry.objects.annotate(
                    chars_length=RawSQL("ARRAY_LENGTH(split_chars_base, 1)", ())
                )
                .filter(
                    site=site,
                    visibility=site.visibility,
                    exclude_from_games=False,
                    exclude_from_kids=False,
                    chars_length__exact=SOLUTION_LENGTH,
                )
                .exclude(title__contains=" ")
                .order_by("custom_order")
                .values_list("title", flat=True)
            )
            caches[CACHE_KEY_WORDSY].set(cache_key_words, words_qs, cache_expiry)

        if len(words_qs):
            seed = get_wordsy_solution_seed(len(words_qs))
            solution = words_qs[seed]
        else:
            solution = ""

        return Response(
            data={
                "orthography": orthography_qs,
                "words": words_qs,
                "valid_guesses": words_qs,  # to be expanded later with phrases that satisfy criteria
                "solution": solution,
            }
        )
