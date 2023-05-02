from secrets import choice

from django.utils.timezone import datetime, timedelta
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets

from backend.models.dictionary import DictionaryEntry, WordOfTheDay
from backend.predicates import utils
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
                )
            )
        else:
            return DictionaryEntry.objects.none()


@extend_schema_view(
    list=extend_schema(
        description="Returns a word of the day for the given site.",
        responses={
            200: DictionaryEntryDetailSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site"),
            404: OpenApiResponse(description="Todo: Site not found"),
        },
    ),
)
class WordOfTheDayView(
    SiteContentViewSetMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    Picks and returns word-of-the-day for a given site.
    """

    http_method_names = ["get"]
    serializer_class = DictionaryEntryDetailSerializer
    pagination_class = None

    @staticmethod
    def get_suitable_queryset(site_slug):
        # Check if there is a word assigned word-of-the-day date of today
        today = datetime.today()
        wotd_obj = WordOfTheDay.objects.filter(site__slug=site_slug, date=today).first()
        if wotd_obj is not None:
            queryset = DictionaryEntry.objects.filter(id=wotd_obj.dictionary_entry.id)
            if queryset.count() > 0:
                return queryset

        # If no words found with today's date, Get words which have not yet been assigned word-of-the-day
        queryset = DictionaryEntry.objects.filter(
            site__slug=site_slug,
            type=DictionaryEntry.TypeOfDictionaryEntry.WORD,
            exclude_from_wotd=False,
            wotd_set=None,
        )
        if queryset.count() > 0:
            selected_word = queryset.first()
            new_wotd_obj = WordOfTheDay(
                date=today, dictionary_entry=selected_word, site=selected_word.site
            )
            new_wotd_obj.save()
            return queryset

        # If no words found satisfying any of the above condition, try to find wotd which has not been assigned a
        # date in the last year
        last_year_date = today - timedelta(weeks=52)
        old_wotd = (
            WordOfTheDay.objects.filter(site__slug=site_slug, date__lte=last_year_date)
            .order_by("date")
            .first()
        )
        if old_wotd is not None:
            queryset = DictionaryEntry.objects.filter(id=old_wotd.dictionary_entry.id)
            WordOfTheDay.objects.filter(id=old_wotd.id).update(date=today)
            if queryset.count() > 0:
                return queryset

        # If there is no word that passes any of the above conditions, choose a word at random
        primary_keys_list = DictionaryEntry.objects.filter(
            site__slug=site_slug,
            type=DictionaryEntry.TypeOfDictionaryEntry.WORD,
            exclude_from_wotd=False,
        ).values_list("id", flat=True)
        random_entry = choice(primary_keys_list)
        WordOfTheDay.objects.filter(dictionary_entry__id=random_entry).update(
            date=today
        )
        return DictionaryEntry.objects.filter(id=random_entry)

    def get_queryset(self):
        site = self.get_validated_site()
        # Logic to select
        if site.count() > 0:
            queryset = self.get_suitable_queryset(site[0].slug)
        else:
            queryset = DictionaryEntry.objects.none()

        # Pulling the first element from viewable words
        words = utils.filter_by_viewable(self.request.user, queryset)
        return words[:1]
