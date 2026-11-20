from calendar import monthrange

from django.conf import settings
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import viewsets
from rest_framework.response import Response

from backend.permissions import predicates
from backend.serializers.analytics_serializers import (
    SiteAnalyticsQuerySerializer,
    SiteAnalyticsSerializer,
)
from backend.utils.matomo_utils import get_monthly_visitors
from backend.views import doc_strings
from backend.views.api_doc_variables import site_slug_parameter
from backend.views.base_views import (
    SiteContentViewSetMixin,
    raise_permission_denied_for_user,
)


@extend_schema_view(
    list=extend_schema(
        description=(
            "Monthly visitor analytics for a Language Site. A visit counts if it "
            "includes the site homepage or any subpage. A visit touching multiple "
            "Language Sites can count toward each. The date selects its containing "
            "calendar month, with both returned boundaries inclusive. Current-month "
            "counts are incomplete and may change. Metric values are null "
            "when unavailable, not zero."
        ),
        parameters=[site_slug_parameter, SiteAnalyticsQuerySerializer],
        responses={
            200: SiteAnalyticsSerializer,
            400: OpenApiResponse(
                description="Invalid date or period. Unknown query parameters are ignored."
            ),
            401: OpenApiResponse(description="Authentication is required."),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
            502: OpenApiResponse(
                description="Matomo failed or returned an invalid report."
            ),
            503: OpenApiResponse(description="Analytics is not configured."),
            504: OpenApiResponse(description="Matomo did not respond in time."),
        },
        examples=[
            OpenApiExample(
                "Monthly site analytics",
                value={
                    "scope": {"type": "site", "slug": "lilwat"},
                    "period": {
                        "type": "month",
                        "startDate": "2026-10-01",
                        "endDate": "2026-10-31",
                        "timezone": "America/Vancouver",
                    },
                    "metrics": {"totalVisits": 590, "uniqueVisitors": 364},
                },
                response_only=True,
            ),
        ],
    ),
)
class SiteAnalyticsViewSet(SiteContentViewSetMixin, viewsets.ViewSet):
    def initial(self, *args, **kwargs):
        super().initial(*args, **kwargs)

        site = self.get_validated_site()
        if not predicates.is_at_least_language_admin(self.request.user, site):
            raise_permission_denied_for_user(self.request.user)

    def list(self, request, *args, **kwargs):
        site = self.get_validated_site()
        query_serializer = SiteAnalyticsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        report_date = query_serializer.validated_data["date"]

        # Regardless of the period, we calculate the start and end dates for the month of the report date.
        start_date = report_date.replace(day=1)
        last_day = monthrange(report_date.year, report_date.month)[1]
        end_date = report_date.replace(day=last_day)
        metrics = get_monthly_visitors(site.slug, start_date)

        analytics = {
            "scope": {"type": "site", "slug": site.slug},
            "period": {
                "type": query_serializer.validated_data["period"],
                "start_date": start_date,
                "end_date": end_date,
                "timezone": settings.TIME_ZONE,
            },
            "metrics": metrics,
        }
        serializer = SiteAnalyticsSerializer(analytics)
        return Response(serializer.data)
