from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.response import Response

from backend.models import Character, DictionaryEntry
from backend.permissions.permission_classes import CanViewTeamContent
from backend.serializers.health_metrics_serializers import SiteHealthMetricsSerializer
from backend.views import doc_strings
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of health metrics for a given site.",
        responses={
            200: SiteHealthMetricsSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter],
    ),
)
class HealthMetricsViewSet(SiteContentViewSetMixin, viewsets.ViewSet):
    """API endpoint that returns health metrics about the specified site."""

    permission_classes = [CanViewTeamContent]

    def list(self, request, *args, **kwargs):
        site = self.get_validated_site()
        health_metrics = self.calculate_health_metrics(site)
        return Response(health_metrics)

    @staticmethod
    def calculate_completion_percentage_metrics(item_counts, total_items):
        """Add percentage completion metrics to the health metrics counts."""
        metrics = {}
        for key, count in item_counts.items():
            completion_percentage = (
                100 - (count / total_items * 100) if total_items else 100
            )
            metrics[key] = {
                "total": count,
                "completion_percentage": round(completion_percentage),
            }

        return metrics

    def calculate_entry_health_metrics(self, entries_qs):
        """Calculate health metrics for dictionary entries in a site."""
        total_entries = entries_qs.count()

        aggregates = {
            "entries_without_audio": Count(
                "id", filter=Q(related_audio__isnull=True), distinct=True
            ),
            "entries_without_categories": Count(
                "id", filter=Q(categories__isnull=True), distinct=True
            ),
            "entries_without_images": Count(
                "id", filter=Q(related_images__isnull=True), distinct=True
            ),
            "entries_without_related_entries": Count(
                "id", filter=Q(related_dictionary_entries__isnull=True), distinct=True
            ),
            "entries_without_translations": Count(
                "id", filter=Q(translations=[]), distinct=True
            ),
        }

        return self.calculate_completion_percentage_metrics(
            entries_qs.aggregate(**aggregates), total_entries
        )

    def calculate_character_health_metrics(self, characters_qs):
        """Calculate health metrics for characters in a site."""
        total_characters = characters_qs.count()

        aggregates = {
            "characters_without_audio": Count(
                "id", filter=Q(related_audio__isnull=True), distinct=True
            ),
            "characters_without_images": Count(
                "id", filter=Q(related_images__isnull=True), distinct=True
            ),
            "characters_without_related_entries": Count(
                "id", filter=Q(related_dictionary_entries__isnull=True), distinct=True
            ),
        }

        return self.calculate_completion_percentage_metrics(
            characters_qs.aggregate(**aggregates), total_characters
        )

    def calculate_health_metrics(self, site):
        """Calculate health metrics for a given site."""
        entries_qs = DictionaryEntry.objects.filter(site=site)
        characters_qs = Character.objects.filter(site=site)

        site_health_metrics = {
            "entries": self.calculate_entry_health_metrics(entries_qs),
            "characters": self.calculate_character_health_metrics(characters_qs),
        }

        return site_health_metrics
