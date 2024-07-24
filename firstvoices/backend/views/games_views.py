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
from backend.views import doc_strings
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
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
)
class WordsyViewSet(SiteContentViewSetMixin, GenericViewSet):
    http_method_names = ["get"]
    pagination_class = None
    queryset = ""

    def list(self, request, **kwargs):
        site = self.get_validated_site()

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
        words = caches[CACHE_KEY_WORDSY].get(cache_key_words)
        if words is None:
            # Filtering words based on their length excluding spaces
            words_qs = (
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
                .order_by("title", "custom_order")
                .distinct("title")
                .values_list("split_chars_base", flat=True)
            )
            words = []
            for split_chars in words_qs.iterator():
                title_from_base_chars = "".join(split_chars)
                if title_from_base_chars not in words:
                    words.append(title_from_base_chars)
            caches[CACHE_KEY_WORDSY].set(cache_key_words, words, cache_expiry)

        if len(words):
            seed = get_wordsy_solution_seed(len(words))
            solution = words[seed]
        else:
            solution = ""

        return Response(
            data={
                "orthography": orthography_qs,
                "words": words,
                "valid_guesses": words,  # to be expanded later with phrases that satisfy criteria
                "solution": solution,
            }
        )
