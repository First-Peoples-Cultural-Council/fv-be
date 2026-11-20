from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers


class SiteAnalyticsQuerySerializer(serializers.Serializer):
    period = serializers.ChoiceField(
        choices=["month"],
        default="month",
        help_text="Reporting period.",
    )
    date = serializers.DateField(
        help_text=(
            "Required query parameter in YYYY-MM-DD format. For example, "
            "2026-10-01 selects all of October 2026. Any date in the same month "
            "selects the same report."
        ),
    )

    def validate_date(self, value):
        today = timezone.localdate(timezone=ZoneInfo(settings.TIME_ZONE))
        if value > today:
            raise serializers.ValidationError("The date cannot be in the future.")
        return value


class AnalyticsScopeSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["site"])
    slug = serializers.SlugField()


class AnalyticsPeriodSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["month"])
    startDate = serializers.DateField(
        source="start_date",
        read_only=True,
        help_text="Calculated first day of the selected month. Response only, not a query parameter.",
    )
    endDate = serializers.DateField(
        source="end_date",
        read_only=True,
        help_text="Calculated last day of the selected month, inclusive. Response only, not a query parameter.",
    )
    timezone = serializers.CharField()


class VisitorMetricsSerializer(serializers.Serializer):
    totalVisits = serializers.IntegerField(
        source="total_visits",
        min_value=0,
        allow_null=True,
        help_text="Number of visits (sessions), or null when unavailable.",
    )
    uniqueVisitors = serializers.IntegerField(
        source="unique_visitors",
        min_value=0,
        allow_null=True,
        help_text=(
            "Distinct visitors across the entire month, or null when unavailable."
        ),
    )


@extend_schema_serializer(many=False)
class SiteAnalyticsSerializer(serializers.Serializer):
    scope = AnalyticsScopeSerializer()
    period = AnalyticsPeriodSerializer()
    metrics = VisitorMetricsSerializer()
