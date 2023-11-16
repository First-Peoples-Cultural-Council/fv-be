from datetime import timedelta

from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.response import Response

from backend.models import DictionaryEntry, Song, Story
from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.models.media import Audio, Image, Video
from backend.views import doc_strings
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of statistics about a given site.",
        responses={
            200: Response,
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
    def calculate_aggregate_stats(queryset_list, has_visibility=False):
        """Calculate aggregate statistics for a given queryset of objects"""
        aggregate_stats = {
            "total": len(queryset_list),
            "available_in_childrens_archive": len(
                [obj for obj in queryset_list if obj.exclude_from_kids is False]
            ),
        }

        # check if visibility field is present on queryset model
        if has_visibility:
            aggregate_stats["public"] = len(
                [obj for obj in queryset_list if obj.visibility == Visibility.PUBLIC]
            )
        return aggregate_stats

    @staticmethod
    def calculate_individual_temporal_stats(
        queryset_list, time_range, has_visibility=False
    ):
        """Calculate temporal statistics for a given queryset of objects from a specified time range"""

        individual_temporal_stats = {
            "created": len(
                [
                    obj
                    for obj in queryset_list
                    if time_range[0] <= obj.created <= time_range[1]
                ]
            ),
            "last_modified": len(
                [
                    obj
                    for obj in queryset_list
                    if time_range[0] <= obj.last_modified <= time_range[1]
                ]
            ),
        }

        if has_visibility:
            individual_temporal_stats["public"] = len(
                [
                    obj
                    for obj in queryset_list
                    if time_range[0] <= obj.last_modified <= time_range[1]
                    and obj.visibility == Visibility.PUBLIC
                ]
            )
            individual_temporal_stats["members"] = len(
                [
                    obj
                    for obj in queryset_list
                    if time_range[0] <= obj.last_modified <= time_range[1]
                    and obj.visibility == Visibility.MEMBERS
                ]
            )
            individual_temporal_stats["team"] = len(
                [
                    obj
                    for obj in queryset_list
                    if time_range[0] <= obj.last_modified <= time_range[1]
                    and obj.visibility == Visibility.TEAM
                ]
            )

        return individual_temporal_stats

    def calculate_temporal_stats(self, queryset, has_visibility=False):
        """Calculate temporal statistics for a given queryset of objects"""
        # Calculate time deltas
        now = timezone.now()
        last_year = now - timedelta(days=365)
        last_6_months = now - timedelta(days=183)
        last_3_months = now - timedelta(days=91)
        last_month = now - timedelta(days=30)
        last_week = now - timedelta(days=7)
        last_3_days = now - timedelta(days=3)
        today = now - timedelta(days=1)

        temporal_stats = {
            "last_year": self.calculate_individual_temporal_stats(
                queryset, (last_year, now), has_visibility
            ),
            "last_6_months": self.calculate_individual_temporal_stats(
                queryset, (last_6_months, now), has_visibility
            ),
            "last_3_months": self.calculate_individual_temporal_stats(
                queryset, (last_3_months, now), has_visibility
            ),
            "last_month": self.calculate_individual_temporal_stats(
                queryset, (last_month, now), has_visibility
            ),
            "last_week": self.calculate_individual_temporal_stats(
                queryset, (last_week, now), has_visibility
            ),
            "last_3_days": self.calculate_individual_temporal_stats(
                queryset, (last_3_days, now), has_visibility
            ),
            "today": self.calculate_individual_temporal_stats(
                queryset, (today, now), has_visibility
            ),
        }

        return temporal_stats

    def calculate_site_stats(self):
        """Calculate statistics for the specified site."""
        site = self.get_validated_site()
        site_slug = site[0].slug

        # Model query sets
        words_qs = list(
            DictionaryEntry.objects.filter(
                site__slug=site_slug, type=TypeOfDictionaryEntry.WORD
            )
        )
        phrases_qs = list(
            DictionaryEntry.objects.filter(
                site__slug=site_slug, type=TypeOfDictionaryEntry.PHRASE
            )
        )
        songs_qs = list(Song.objects.filter(site__slug=site_slug))
        stories_qs = list(Story.objects.filter(site__slug=site_slug))
        images_qs = list(Image.objects.filter(site__slug=site_slug))
        audio_qs = list(Audio.objects.filter(site__slug=site_slug))
        video_qs = list(Video.objects.filter(site__slug=site_slug))

        # Calculate aggregate stats from site models
        site_aggregate_stats = {
            "words": self.calculate_aggregate_stats(words_qs, has_visibility=True),
            "phrases": self.calculate_aggregate_stats(phrases_qs, has_visibility=True),
            "songs": self.calculate_aggregate_stats(songs_qs, has_visibility=True),
            "stories": self.calculate_aggregate_stats(stories_qs, has_visibility=True),
            "images": self.calculate_aggregate_stats(images_qs),
            "audio": self.calculate_aggregate_stats(audio_qs),
            "video": self.calculate_aggregate_stats(video_qs),
        }

        # Calculate temporal stats from site models
        site_temporal_stats = {
            "words": self.calculate_temporal_stats(words_qs, has_visibility=True),
            "phrases": self.calculate_temporal_stats(phrases_qs, has_visibility=True),
            "songs": self.calculate_temporal_stats(songs_qs, has_visibility=True),
            "stories": self.calculate_temporal_stats(stories_qs, has_visibility=True),
            "images": self.calculate_temporal_stats(images_qs),
            "audio": self.calculate_temporal_stats(audio_qs),
            "video": self.calculate_temporal_stats(video_qs),
        }

        site_stats = {
            "aggregate": site_aggregate_stats,
            "temporal": site_temporal_stats,
        }

        return site_stats
