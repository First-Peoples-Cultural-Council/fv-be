from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import parsers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.import_jobs import ImportJob, JobStatus
from backend.serializers.import_job_serializers import ImportJobSerializer
from backend.tasks.import_job_tasks import batch_import
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from firstvoices.celery import link_error_handler


@extend_schema_view(
    list=extend_schema(
        description=_(
            "A list of batch import jobs associated with the specified site."
        ),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=ImportJobSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description=_("Details about a specific batch import job."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=ImportJobSerializer,
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
        description=_("Add a batch import job."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=ImportJobSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class ImportJobViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    serializer_class = ImportJobSerializer
    http_method_names = ["get", "post", "delete"]
    parser_classes = [
        parsers.FormParser,
        parsers.MultiPartParser,  # to support file uploads
        parsers.JSONParser,
    ]

    permission_type_map = {
        **FVPermissionViewSetMixin.permission_type_map,
        "confirm": "change",
    }

    def get_queryset(self):
        site = self.get_validated_site()
        return ImportJob.objects.filter(site=site).order_by(
            "-created"
        )  # permissions are applied by the base view

    def perform_create(self, serializer):
        instance = serializer.save()

        # Dry-run to get validation results
        transaction.on_commit(
            lambda: batch_import.apply_async(
                (str(instance.id),), link_error=link_error_handler.s()
            )
        )

    @action(detail=True, methods=["post"])
    def confirm(self, request, site_slug=None, pk=None):
        site = self.get_validated_site()
        import_job = self.get_validated_import_job(site)

        import_job.status = JobStatus.STARTED
        import_job.save()

        # Start the task
        transaction.on_commit(
            lambda: batch_import.apply_async(
                (str(import_job.id), False), link_error=link_error_handler.s()
            )
        )

        # Update the in-memory instance and return the job
        import_job = self.get_validated_import_job(site)
        serializer = ImportJobSerializer(
            import_job, context={"request": self.request, "site": site}
        )
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers
        )

    def get_validated_import_job(self, site):
        import_job_id = self.kwargs["pk"]
        try:
            import_job = ImportJob.objects.filter(pk=import_job_id)
        except ValidationError:
            # story id is not a valid uuid
            raise Http404

        if len(import_job) == 0:
            raise Http404

        return import_job.first()
