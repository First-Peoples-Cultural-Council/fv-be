import math

from django.core.cache import caches
from django.db.models.expressions import RawSQL
from django.utils.timezone import datetime
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from backend.models import Character, DictionaryEntry
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.utils.character_utils import UNKNOWN_FLAG
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin

CACHE_KEY_WORDSY = "wordsy"
SOLUTION_LENGTH = 5


def get_wordsy_solution_seed(num_words):
    # inspired from previous fv-wordsy game
    epoch = datetime(2024, 1, 1, 0, 0, 0).timestamp()  # wordsy game epoch
    now = datetime.now().timestamp()
    seconds_in_day = 86400
    index = math.floor((now - epoch) / seconds_in_day)
    return index % num_words


def get_wordsy_possible_solutions(site):
    """Get friendly words with custom length matching the number of game letters."""
    words_qs = (
        # filter words based on custom length; this also filters out unknown chars
        DictionaryEntry.objects.annotate(
            custom_char_length=RawSQL("ARRAY_LENGTH(split_chars_base, 1)", ())
        )
        # visible, kid-friendly, and games-friendly words only
        .filter(
            site=site,
            visibility=site.visibility,
            type=TypeOfDictionaryEntry.WORD,
            exclude_from_games=False,
            exclude_from_kids=False,
            custom_char_length__exact=SOLUTION_LENGTH,
        )
        # words cannot contain spaces
        .exclude(title__contains=" ")
        .exclude(custom_order__contains=UNKNOWN_FLAG)
        .order_by("custom_order")
        .distinct("custom_order")
        .values_list("split_chars_base", flat=True)
    )
    solutions = []
    for split_chars in words_qs.iterator():
        title_as_base_chars = "".join(split_chars)
        solutions.append(title_as_base_chars)
    return solutions


def get_wordsy_possible_guesses(site):
    """Get all words with custom length matching the number of game letters."""
    # this can be amended later to get possible tokens in more complex ways.
    # for now, match how solution words are found but with fewer restrictions.
    entries_qs = (
        DictionaryEntry.objects.annotate(
            custom_char_length=RawSQL("ARRAY_LENGTH(split_chars_base, 1)", ())
        )
        .filter(
            site=site,
            visibility=site.visibility,
            custom_char_length=SOLUTION_LENGTH,
        )
        .exclude(title__contains=" ")
        .exclude(custom_order__contains=UNKNOWN_FLAG)
        .order_by("custom_order")
        .distinct("custom_order")
        .values_list("split_chars_base", flat=True)
    )
    guesses = []
    for split_chars in entries_qs.iterator():
        title_as_base_chars = "".join(split_chars)
        if title_as_base_chars not in guesses:
            guesses.append(title_as_base_chars)
    return guesses


@extend_schema_view(
    list=extend_schema(
        description="Returns the wordsy config for the day.",
        responses={
            200: inline_serializer(
                name="wordsy_response",
                fields={
                    "orthography": serializers.ListField(),
                    "words": serializers.ListField(),
                    "validGuesses": serializers.ListField(),
                    "solution": serializers.CharField(),
                },
            ),
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
        parameters=[site_slug_parameter],
    ),
)
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
        cache_key_guesses = f"{site.title}-guesses"

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

        # friendly words
        words = caches[CACHE_KEY_WORDSY].get(cache_key_words)
        if words is None:
            words = get_wordsy_possible_solutions(site=site)
            caches[CACHE_KEY_WORDSY].set(cache_key_words, words, cache_expiry)

        # possible guesses
        guesses = caches[CACHE_KEY_WORDSY].get(cache_key_guesses)
        if guesses is None:
            # don't bother searching for guesses if there are no friendly words
            if len(words):
                guesses = get_wordsy_possible_guesses(site=site)
                caches[CACHE_KEY_WORDSY].set(cache_key_words, words, cache_expiry)
            else:
                guesses = words

        # today's solution
        if len(words):
            seed = get_wordsy_solution_seed(len(words))
            solution = words[seed]
        else:
            solution = ""

        return Response(
            data={
                "orthography": orthography_qs,
                "words": words,
                "valid_guesses": guesses,
                "solution": solution,
            }
        )
