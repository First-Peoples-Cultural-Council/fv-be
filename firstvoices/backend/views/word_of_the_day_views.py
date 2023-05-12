from secrets import choice

from django.utils.timezone import datetime, timedelta
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from backend.models.dictionary import DictionaryEntry, WordOfTheDay
from backend.permissions import utils
from backend.serializers.word_of_the_day_serializers import WordOfTheDayListSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="Returns a word of the day for the given site.",
        responses={
            200: WordOfTheDayListSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
)
class WordOfTheDayView(
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    mixins.ListModelMixin,
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
    def get_unassigned_word(site_slug, today):
        # Returns words which have not yet been assigned as a word of the day
        # also adds a word of the day entry for it
        words_used = WordOfTheDay.objects.filter(site__slug=site_slug).values_list(
            "dictionary_entry_id", flat=True
        )
        dictionary_entry_queryset = DictionaryEntry.objects.filter(
            site__slug=site_slug,
            type=DictionaryEntry.TypeOfDictionaryEntry.WORD,
            exclude_from_wotd=False,
        ).exclude(id__in=list(words_used))
        if dictionary_entry_queryset.count() > 0:
            selected_word = dictionary_entry_queryset.first()
            wotd_entry = WordOfTheDay(
                date=today, dictionary_entry=selected_word, site=selected_word.site
            )
            wotd_entry.save()
            return WordOfTheDay.objects.filter(id=wotd_entry.id)
        else:
            return WordOfTheDay.objects.none()

    @staticmethod
    def get_wotd_before_date(site_slug, today, given_date):
        # filters words which have been used since the given date, then picks a random word from the older words
        words_used_since_given_date = (
            WordOfTheDay.objects.filter(site__slug=site_slug)
            .filter(date__gte=given_date)
            .order_by("dictionary_entry__id")
            .distinct("dictionary_entry__id")
            .values_list("dictionary_entry__id", flat=True)
        )
        random_old_word = (
            WordOfTheDay.objects.exclude(
                dictionary_entry__id__in=words_used_since_given_date
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
    def get_random_word_as_wotd(site_slug, today):
        # Returns a random word and adds a word of the day entry for it
        primary_keys_list = DictionaryEntry.objects.filter(
            site__slug=site_slug,
            type=DictionaryEntry.TypeOfDictionaryEntry.WORD,
            exclude_from_wotd=False,
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

    def get_selected_word(self, site_slug):
        # Goes over a few conditions to find a suitable word of the day

        # Case 1. Check if there is a word assigned word-of-the-day date of today
        today = datetime.today()
        selected_word = WordOfTheDay.objects.filter(site__slug=site_slug, date=today)
        if selected_word.count() == 0:
            # Case 2. If no words found with today's date, Get words which have not yet been assigned word-of-the-day
            selected_word = self.get_unassigned_word(site_slug, today)
        if selected_word.count() == 0:
            # Case 3. If no words found satisfying any of the above condition, try to find wotd which has not
            # been assigned a date in the last year
            last_year_date = today - timedelta(weeks=52)
            selected_word = self.get_wotd_before_date(site_slug, today, last_year_date)
        if selected_word.count() == 0:
            # Case 4. If there is no word that passes any of the above conditions, choose a word at random
            random_word = self.get_random_word_as_wotd(site_slug, today)
            return random_word

        return selected_word

    def list(self, request, *args, **kwargs):
        # Overriding list method from FVPermissionViewSetMixin to only get the first word
        site = self.get_validated_site()

        # Logic to select queryset
        selected_word = self.get_selected_word(site[0].slug)
        queryset = utils.filter_by_viewable(request.user, selected_word)

        # serialize and return the data, with context to support hyperlinking
        serializer = self.serializer_class(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)
