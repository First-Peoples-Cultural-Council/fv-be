from secrets import choice

from django.db.models import F, Prefetch
from django.utils.timezone import datetime, timedelta
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from backend.models import Image
from backend.models.dictionary import (
    DictionaryEntry,
    TypeOfDictionaryEntry,
    WordOfTheDay,
)
from backend.models.media import Audio, Video
from backend.permissions import utils
from backend.serializers.word_of_the_day_serializers import WordOfTheDayListSerializer
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import (
    DictionarySerializerContextMixin,
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
)
from backend.views.utils import get_media_prefetch_list, get_select_related_media_fields


@extend_schema_view(
    list=extend_schema(
        description="Returns a word of the day for the given site.",
        responses={
            200: WordOfTheDayListSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
        parameters=[site_slug_parameter],
    ),
)
class WordOfTheDayView(
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    mixins.ListModelMixin,
    DictionarySerializerContextMixin,
    viewsets.GenericViewSet,
):
    """
    Picks and returns word-of-the-day for a given site.
    """

    http_method_names = ["get"]
    serializer_class = WordOfTheDayListSerializer
    pagination_class = None
    model = WordOfTheDay
    queryset = ""

    @staticmethod
    def get_unassigned_word(site, today):
        # Returns words which have not yet been assigned as a word of the day
        # also adds a word of the day entry for it
        words_used = WordOfTheDay.objects.filter(site=site).values_list(
            "dictionary_entry_id", flat=True
        )
        dictionary_entry_queryset = DictionaryEntry.objects.filter(
            site=site,
            type=TypeOfDictionaryEntry.WORD,
            exclude_from_wotd=False,
            visibility=F("site__visibility"),
        ).exclude(id__in=list(words_used))
        if len(dictionary_entry_queryset) > 0:
            selected_word = dictionary_entry_queryset.first()
            wotd_entry = WordOfTheDay(
                date=today, dictionary_entry=selected_word, site=selected_word.site
            )
            wotd_entry.save()
            return WordOfTheDay.objects.filter(id=wotd_entry.id)
        else:
            return WordOfTheDay.objects.none()

    @staticmethod
    def get_wotd_before_date(site, today, given_date):
        # filters words which have been used since the given date, then picks a random word from the older words
        words_used_since_given_date = (
            WordOfTheDay.objects.filter(site=site)
            .filter(date__gte=given_date)
            .order_by("dictionary_entry__id")
            .distinct("dictionary_entry__id")
            .values_list("dictionary_entry__id", flat=True)
        )
        random_old_word = (
            WordOfTheDay.objects.filter(site=site)
            .exclude(dictionary_entry__id__in=words_used_since_given_date)
            .filter(
                dictionary_entry__visibility=F("dictionary_entry__site__visibility")
            )
            .order_by("?")
            .first()
        )
        if random_old_word:
            wotd_entry = WordOfTheDay(
                date=today,
                dictionary_entry=random_old_word.dictionary_entry,
                site=random_old_word.dictionary_entry.site,
            )
            wotd_entry.save()
            return WordOfTheDay.objects.filter(id=wotd_entry.id)
        else:
            return WordOfTheDay.objects.none()

    @staticmethod
    def get_random_word_as_wotd(site, today):
        # Returns a random word and adds a word of the day entry for it
        primary_keys_list = DictionaryEntry.objects.filter(
            site=site,
            type=TypeOfDictionaryEntry.WORD,
            exclude_from_wotd=False,
            visibility=F("site__visibility"),
        ).values_list("id", flat=True)
        if len(primary_keys_list) == 0:
            # No words found
            return DictionaryEntry.objects.none()
        random_word_id = choice(primary_keys_list)
        random_word = DictionaryEntry.objects.get(id=random_word_id)
        wotd_entry = WordOfTheDay(
            date=today, dictionary_entry=random_word, site=random_word.site
        )
        wotd_entry.save()
        return WordOfTheDay.objects.filter(id=wotd_entry.id)

    def get_selected_word(self, site):
        # Goes over a few conditions to find a suitable word of the day

        # Case 1. Check if there is a word assigned word-of-the-day date of today
        today = datetime.today()
        selected_word = WordOfTheDay.objects.filter(site=site, date=today)
        if len(selected_word) == 0:
            # Case 2. If no words found with today's date, Get words which have not yet been assigned word-of-the-day
            selected_word = self.get_unassigned_word(site, today)
        if len(selected_word) == 0:
            # Case 3. If no words found satisfying any of the above condition, try to find wotd which has not
            # been assigned a date in the last year
            last_year_date = today - timedelta(weeks=52)
            selected_word = self.get_wotd_before_date(site, today, last_year_date)
        if len(selected_word) == 0:
            # Case 4. If there is no word that passes any of the above conditions, choose a word at random
            random_word = self.get_random_word_as_wotd(site, today)
            return random_word

        return selected_word

    def list(self, request, *args, **kwargs):
        # Overriding list method from FVPermissionViewSetMixin to only get the first word
        site = self.get_validated_site()
        selected_word = self.get_selected_word(site)

        queryset = WordOfTheDay.objects.none()

        if selected_word:
            unfiltered_queryset = DictionaryEntry.objects.filter(
                id=selected_word[0].dictionary_entry.id
            )
            filtered_queryset = utils.filter_by_viewable(
                request.user, unfiltered_queryset
            )
            if filtered_queryset:
                queryset = selected_word

        queryset = queryset.select_related(
            "dictionary_entry",
            "dictionary_entry__site",
            "dictionary_entry__site__language",
            "dictionary_entry__created_by",
            "dictionary_entry__last_modified_by",
            "dictionary_entry__part_of_speech",
        ).prefetch_related(
            "dictionary_entry__acknowledgement_set",
            "dictionary_entry__alternatespelling_set",
            "dictionary_entry__note_set",
            "dictionary_entry__pronunciation_set",
            "dictionary_entry__translation_set",
            "dictionary_entry__categories",
            Prefetch(
                "dictionary_entry__related_dictionary_entries",
                queryset=DictionaryEntry.objects.visible(self.request.user)
                .select_related("site")
                .prefetch_related(
                    "translation_set", *get_media_prefetch_list(self.request.user)
                ),
            ),
            Prefetch(
                "dictionary_entry__related_audio",
                queryset=Audio.objects.visible(self.request.user)
                .select_related("original", "site")
                .prefetch_related("speakers"),
            ),
            Prefetch(
                "dictionary_entry__related_images",
                queryset=Image.objects.visible(self.request.user).select_related(
                    *get_select_related_media_fields(None)
                ),
            ),
            Prefetch(
                "dictionary_entry__related_videos",
                queryset=Video.objects.visible(self.request.user).select_related(
                    *get_select_related_media_fields(None)
                ),
            ),
        )

        # serialize and return the data, with context to support hyperlinking
        serializer = self.serializer_class(
            queryset, many=True, context=self.get_serializer_context()
        )
        return Response(serializer.data)
