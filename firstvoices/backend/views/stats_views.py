from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.response import Response

from backend.models import DictionaryEntry, Song, Story
from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.models.media import Audio, Document, Image, Video
from backend.permissions.filters import view as view_filters
from backend.serializers.stats_serializers import SiteStatsSerializer
from backend.views import doc_strings
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of statistics about a given site.",
        responses={
            200: SiteStatsSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter],
    ),
)
class StatsViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, viewsets.ViewSet):
    """API endpoint that returns statistics about the specified site."""

    def list(self, request, *args, **kwargs):
        """Return a list of statistics about the specified site."""
        site_stats = self.calculate_site_stats()
        return Response(site_stats)

    @staticmethod
    def calculate_aggregate_stats(queryset, has_visibility=False):
        """Calculate aggregate statistics for a given queryset of objects"""
        aggregates = {
            "total": Count("id", distinct=True),
            "available_in_childrens_archive": Count(
                "id",
                filter=Q(exclude_from_kids=False),
                distinct=True,
            ),
        }

        if has_visibility:
            aggregates["public"] = Count(
                "id", filter=Q(visibility=Visibility.PUBLIC), distinct=True
            )
            aggregates["members"] = Count(
                "id", filter=Q(visibility=Visibility.MEMBERS), distinct=True
            )
            aggregates["team"] = Count(
                "id", filter=Q(visibility=Visibility.TEAM), distinct=True
            )

        return queryset.aggregate(**aggregates)

    @staticmethod
    def build_temporal_stats_aggregates(time_range, prefix, has_visibility=False):
        """Create a dictionary of aggregate expressions for temporal stats"""
        temporal_aggregates = {
            f"{prefix}__created__total": Count(
                "id",
                filter=Q(created__range=time_range),
                distinct=True,
            ),
            f"{prefix}__last_modified__total": Count(
                "id",
                filter=Q(last_modified__range=time_range),
                distinct=True,
            ),
        }

        if has_visibility:
            for v in Visibility:
                temporal_aggregates[f"{prefix}__created__{v.name.lower()}"] = Count(
                    "id",
                    filter=Q(created__range=time_range, visibility=v),
                    distinct=True,
                )
                temporal_aggregates[f"{prefix}__last_modified__{v.name.lower()}"] = (
                    Count(
                        "id",
                        filter=Q(last_modified__range=time_range, visibility=v),
                        distinct=True,
                    )
                )

        return temporal_aggregates

    def calculate_temporal_stats(self, queryset, has_visibility=False):
        """Calculate temporal statistics for a given queryset of objects"""
        now = timezone.now()
        time_ranges = {
            "last_year": (now - timedelta(days=365), now),
            "last_6_months": (now - timedelta(days=183), now),
            "last_3_months": (now - timedelta(days=91), now),
            "last_month": (now - timedelta(days=30), now),
            "last_week": (now - timedelta(days=7), now),
            "last_3_days": (now - timedelta(days=3), now),
            "today": (now - timedelta(days=1), now),
        }

        all_temporal_aggregates = {}
        for prefix, time_range in time_ranges.items():
            temporal_aggregates = self.build_temporal_stats_aggregates(
                time_range, prefix, has_visibility=has_visibility
            )
            all_temporal_aggregates.update(temporal_aggregates)

        flat_temporal_stats = queryset.aggregate(**all_temporal_aggregates)

        temporal_stats = {}
        for prefix in time_ranges.keys():
            temporal_stats[prefix] = {
                "created": {
                    "total": flat_temporal_stats[f"{prefix}__created__total"],
                },
                "last_modified": {
                    "total": flat_temporal_stats[f"{prefix}__last_modified__total"],
                },
            }
            if has_visibility:
                for v in Visibility:
                    temporal_stats[prefix]["created"][v.name.lower()] = (
                        flat_temporal_stats[f"{prefix}__created__{v.name.lower()}"]
                    )
                    temporal_stats[prefix]["last_modified"][v.name.lower()] = (
                        flat_temporal_stats[
                            f"{prefix}__last_modified__{v.name.lower()}"
                        ]
                    )

        return temporal_stats

    def calculate_site_stats(self):
        """Calculate statistics for the specified site."""
        site = self.get_validated_site()
        user = self.request.user

        visible_object_filter = view_filters.is_visible_object(user)
        visible_site_filter = view_filters.has_visible_site(user)

        # Content query sets that have visibility fields
        words_qs = DictionaryEntry.objects.filter(
            visible_object_filter, site=site, type=TypeOfDictionaryEntry.WORD
        )

        phrases_qs = DictionaryEntry.objects.filter(
            visible_object_filter, site=site, type=TypeOfDictionaryEntry.PHRASE
        )

        songs_qs = Song.objects.filter(visible_object_filter, site=site)
        stories_qs = Story.objects.filter(visible_object_filter, site=site)

        # Media query sets
        audio_qs = Audio.objects.filter(visible_site_filter, site=site)
        document_qs = Document.objects.filter(visible_site_filter, site=site)
        images_qs = Image.objects.filter(visible_site_filter, site=site)
        video_qs = Video.objects.filter(visible_site_filter, site=site)

        # Calculate aggregate stats from site models
        site_aggregate_stats = {
            "words": self.calculate_aggregate_stats(words_qs, has_visibility=True),
            "phrases": self.calculate_aggregate_stats(phrases_qs, has_visibility=True),
            "songs": self.calculate_aggregate_stats(songs_qs, has_visibility=True),
            "stories": self.calculate_aggregate_stats(stories_qs, has_visibility=True),
            "audio": self.calculate_aggregate_stats(audio_qs),
            "document": self.calculate_aggregate_stats(document_qs),
            "images": self.calculate_aggregate_stats(images_qs),
            "video": self.calculate_aggregate_stats(video_qs),
        }

        # Calculate temporal stats from site models
        site_temporal_stats = {
            "words": self.calculate_temporal_stats(words_qs, has_visibility=True),
            "phrases": self.calculate_temporal_stats(phrases_qs, has_visibility=True),
            "songs": self.calculate_temporal_stats(songs_qs, has_visibility=True),
            "stories": self.calculate_temporal_stats(stories_qs, has_visibility=True),
            "audio": self.calculate_temporal_stats(audio_qs),
            "document": self.calculate_temporal_stats(document_qs),
            "images": self.calculate_temporal_stats(images_qs),
            "video": self.calculate_temporal_stats(video_qs),
        }

        site_stats = {
            "aggregate": site_aggregate_stats,
            "temporal": site_temporal_stats,
        }

        return site_stats
