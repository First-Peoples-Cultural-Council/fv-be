from secrets import choice

from django.utils.timezone import datetime, timedelta
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets

from backend.models import DictionaryEntry
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
        if site.count() > 0:
            return DictionaryEntry.objects.filter(site__slug=site[0].slug)
        else:
            return DictionaryEntry.objects.filter(site__slug=None)


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
        queryset = DictionaryEntry.objects.filter(
            site__slug=site_slug,
            type=DictionaryEntry.TypeOfDictionaryEntry.WORD,
            wotd_enabled=True,
            wotd_date=today,
        )
        if queryset.count() > 0:
            return queryset

        # If no words found with today's date, Get words which have not yet been assigned word-of-the-day
        queryset = DictionaryEntry.objects.filter(
            site__slug=site_slug,
            type=DictionaryEntry.TypeOfDictionaryEntry.WORD,
            wotd_enabled=True,
            wotd_date=None,
        )
        if queryset.count() > 0:
            return queryset

        # If no words found satisfying any of the above condition, try to find wotd which has not been assigned a
        # date in the last year
        last_year_date = today - timedelta(weeks=52)  # can only go upto weeks
        queryset = DictionaryEntry.objects.filter(
            site__slug=site_slug,
            type=DictionaryEntry.TypeOfDictionaryEntry.WORD,
            wotd_enabled=True,
            wotd_date__lte=last_year_date,
        )
        if queryset.count() > 0:
            return queryset

        # If there is no word that passes any of the above conditions, choose a word at random
        primary_keys_list = DictionaryEntry.objects.filter(
            site__slug=site_slug,
            type=DictionaryEntry.TypeOfDictionaryEntry.WORD,
            wotd_enabled=True,
        ).values_list("id", flat=True)
        random_entry = choice(primary_keys_list)
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
