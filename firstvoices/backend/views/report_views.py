from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.viewsets import ModelViewSet

from backend.models import Site

from ..permissions import predicates
from ..serializers.report_serializers import ReportSerializer
from . import doc_strings
from .api_doc_variables import site_slug_parameter


@extend_schema_view(
    list=extend_schema(
        description=_(
            "A list of reports containing metrics about the data on each language site."
        ),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=ReportSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
    retrieve=extend_schema(
        description=_("Data report for a specific language site."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=ReportSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
        ],
    ),
)
class ReportViewSet(ModelViewSet):
    http_method_names = ["get"]
    serializer_class = ReportSerializer
    queryset = Site.objects.select_related("language").all()

    def get(self, **kwargs):
        if self.request.user.is_anonymous:
            raise NotAuthenticated

        if not predicates.is_superadmin(self.request.user, None):
            raise PermissionDenied

        return super().get(**kwargs)
