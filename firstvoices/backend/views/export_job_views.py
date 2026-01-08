from django.db import transaction
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework.viewsets import ModelViewSet

from backend.models.jobs import ExportJob
from backend.serializers.export_job_serializers import ExportJobSerializer
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_search_entries_views import BASE_SEARCH_PARAMS
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from backend.views.search_site_entries_views import SITE_SEARCH_PARAMS


@extend_schema_view(
    list=extend_schema(
        description="A list of all export jobs for the specified site.",
        responses={
            200: ExportJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific export job.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=ExportJobSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description="Creates a new export job. The job can be validated or confirmed using the relevant endpoints.",
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=ExportJobSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            *SITE_SEARCH_PARAMS,
            *BASE_SEARCH_PARAMS,
            OpenApiParameter(
                name="types",
                description="Filter by type of content. Options are word & phrase.",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "",
                        value="",
                        description="Retrieves all types of results.",
                    ),
                    OpenApiExample(
                        "word",
                        value="word",
                        description="Retrieves all words.",
                    ),
                    OpenApiExample(
                        "phrase",
                        value="phrase",
                        description="Retrieves all phrases.",
                    ),
                ],
            ),
        ],
    ),
)
class ExportJobViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    """
    API endpoint that allows export jobs to be viewed.
    """

    http_method_names = ["get", "post"]
    serializer_class = ExportJobSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        return ExportJob.objects.filter(site=site).order_by("created")

    def perform_create(self, serializer):
        serializer.save()
        query_params = self.request.query_params

        # Trigger the search and export csv generation after model creation
        transaction.on_commit(lambda: print("Doing something" + str(query_params)))
