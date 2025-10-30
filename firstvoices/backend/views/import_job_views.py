from django.db import transaction
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import parsers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models import ImportJobMode
from backend.models.import_jobs import ImportJob, JobStatus
from backend.serializers.import_job_serializers import ImportJobSerializer
from backend.tasks.import_job_tasks import confirm_import_job, validate_import_job
from backend.tasks.utils import verify_no_other_import_jobs_running
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import (
    AsyncJobDeleteMixin,
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
)
from firstvoices.celery import link_error_handler


@extend_schema_view(
    list=extend_schema(
        description=_(
            "A list of batch import jobs associated with the specified site. "
            "See the detail view for more information on specified fields."
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
        description=_(
            "Creates a new batch import job. The job can be validated or confirmed using the relevant endpoints."
        ),
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
        ],
    ),
    destroy=extend_schema(
        description="Deletes a single import-job and its associated file and result for the specified site. "
        "This action does not delete any of the entries imported by the import-job.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    confirm=extend_schema(
        description=_(
            "Starts importing the data, as described in the validationReport. In order to succeed, the "
            "validationStatus must already be 'COMPLETE' and there must be no other imports jobs in progress "
            "for the site. When finished, the status will be 'COMPLETE'."
        ),
        responses={
            202: OpenApiResponse(
                description=doc_strings.success_202_job_accepted,
                response=ImportJobSerializer,
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
    validate=extend_schema(
        description=_(
            "Starts validating the data including any newly uploaded media. "
            "When finished, the validationStatus and validationReport will be updated."
        ),
        responses={
            202: OpenApiResponse(description=doc_strings.success_202_job_accepted),
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
class ImportJobViewSet(
    AsyncJobDeleteMixin, SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
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
        "validate": "change",
    }

    started_statuses = [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE]

    started_validation_statuses = [
        JobStatus.ACCEPTED,
        JobStatus.STARTED,
    ]

    import_job_modes = [ImportJobMode.SKIP_DUPLICATES, ImportJobMode.ALLOW_DUPLICATES]

    def get_queryset(self):
        site = self.get_validated_site()
        return ImportJob.objects.filter(
            site=site, mode__in=self.import_job_modes
        ).order_by(
            "-created"
        )  # permissions are applied by the base view

    @action(detail=True, methods=["post"])
    def validate(self, request, site_slug=None, pk=None):
        """
        Method to start the validation process on a given import-job.
        """
        import_job_id = self.kwargs["pk"]
        curr_job = ImportJob.objects.filter(id=import_job_id)[0]

        # Checks to ensure consistency

        # Verify the current job is not running or queued.
        if curr_job.validation_status in self.started_validation_statuses:
            raise ValidationError(
                "This job has already been queued and is currently being validated."
            )

        if curr_job.status in self.started_statuses:
            raise ValidationError(
                "This job has already been confirmed and is currently being imported."
            )

        verify_no_other_import_jobs_running(curr_job)

        # Queue the job for validation
        curr_job.validation_status = JobStatus.ACCEPTED
        curr_job.save()

        transaction.on_commit(
            lambda: validate_import_job.apply_async(
                (str(import_job_id),),
                link_error=link_error_handler.s(),
                ignore_result=True,
            )
        )

        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def confirm(self, request, site_slug=None, pk=None):
        import_job_id = self.kwargs["pk"]

        curr_job = ImportJob.objects.get(id=import_job_id)

        if curr_job.validation_status != JobStatus.COMPLETE:
            raise ValidationError(
                "Please validate the job before confirming the import."
            )

        if curr_job.status in [JobStatus.ACCEPTED, JobStatus.STARTED]:
            raise ValidationError(
                "This job has already been confirmed and is currently being imported."
            )

        if curr_job.status == JobStatus.COMPLETE:
            raise ValidationError("This job has already finished importing.")

        verify_no_other_import_jobs_running(curr_job)

        curr_job.status = JobStatus.ACCEPTED
        curr_job.save()

        # Start the task
        transaction.on_commit(
            lambda: confirm_import_job.apply_async(
                (str(curr_job.id),),
                link_error=link_error_handler.s(),
                ignore_result=True,
            )
        )

        return Response(status=status.HTTP_202_ACCEPTED)

    def perform_destroy(self, instance):
        if instance.validation_status in self.started_validation_statuses:
            raise ValidationError(
                f"This job cannot be deleted as it is being validated. "
                f"This job has the validation status: {instance.status}"
            )

        super().perform_destroy(instance)
