from django.db import transaction
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import parsers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.import_jobs import ImportJob, JobStatus
from backend.serializers.import_job_serializers import ImportJobSerializer
from backend.tasks.import_job_tasks import (
    batch_import,
    get_import_jobs_queued_or_running,
)
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
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
            "Creates a new batch import job and automatically starts generating a validation report. "
            "Once the validationStatus is 'COMPLETE', the validationReport will list how many rows can "
            "be imported, ignored columns, rows or any errors. See the 'confirm' API to import the data."
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
            id_parameter,
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
        "validate": "change",
    }

    def get_queryset(self):
        site = self.get_validated_site()
        return ImportJob.objects.filter(site=site).order_by(
            "-created"
        )  # permissions are applied by the base view

    def perform_create(self, serializer):
        instance = serializer.save()

        # Accepting the job for validation
        instance.validation_status = JobStatus.STARTED
        instance.save()

        # Dry-run to get validation results
        transaction.on_commit(
            lambda: batch_import.apply_async(
                (
                    str(instance.id),
                    True,
                ),
                link_error=link_error_handler.s(),
                ignore_result=True,
            )
        )

    @action(detail=True, methods=["post"])
    def confirm(self, request, site_slug=None, pk=None):
        import_job_id = self.kwargs["pk"]

        site = self.get_validated_site()
        import_job = ImportJob.objects.get(id=import_job_id)

        # if its already started or queued, do not queue the job again
        if import_job.status == JobStatus.STARTED:
            raise ValidationError(
                "The specified job is already running or queued. It cannot be run again once the import is finished."
            )

        # If the job status is already completed, abort the task
        if import_job.status in [JobStatus.COMPLETE, JobStatus.FAILED]:
            raise ValidationError(
                "The job has already been executed once. "
                "Please create another batch request to import the entries."
            )

        # If dry-run has not been executed successfully, do not proceed for the db import
        if import_job.validation_status == JobStatus.STARTED:
            raise ValidationError(
                "It seems a dry-run is still in progress. "
                "Please wait for it to finish before proceeding with the import."
            )
        if import_job.validation_status in [
            JobStatus.ACCEPTED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        ]:
            raise ValidationError(
                "A successful dry-run is required before doing the import. "
                "Please fix any issues found during the dry-run of the CSV file and re-validate or run a new batch."
            )

        # Verify that no other jobs are started or queued for the same site
        existing_incomplete_jobs = get_import_jobs_queued_or_running(
            site, import_job_id
        )

        if len(existing_incomplete_jobs):
            raise ValidationError(
                "There is at least 1 job on this site that is already running or queued to run soon. "
                "Please wait for it to finish before starting a new one."
            )

        import_job.status = JobStatus.STARTED
        import_job.save()

        # Start the task
        transaction.on_commit(
            lambda: batch_import.apply_async(
                (
                    str(import_job.id),
                    False,
                ),
                link_error=link_error_handler.s(),
                ignore_result=True,
            )
        )

        # Update the in-memory instance and return the job
        import_job = ImportJob.objects.get(id=import_job_id)
        serializer = ImportJobSerializer(
            import_job, context={"request": self.request, "site": site}
        )
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_202_ACCEPTED, headers=headers
        )

    @action(detail=True, methods=["post"])
    def validate(self, request, site_slug=None, pk=None):
        """
        Method to start the validation process on a given import-job.
        """
        site = self.get_validated_site()
        import_job_id = self.kwargs["pk"]

        # Verify that no other jobs are started or queued for the same site
        existing_incomplete_jobs = get_import_jobs_queued_or_running(
            site, import_job_id
        )

        if len(existing_incomplete_jobs):
            raise ValidationError(
                "There is at least 1 job on this site that is already running or queued to run soon. "
                "Please wait for it to finish before starting a new one."
            )

        # if its already running or queued for dry run, do not queue the job again
        curr_job = ImportJob.objects.filter(id=import_job_id)[0]
        if curr_job.validation_status in [JobStatus.ACCEPTED, JobStatus.STARTED]:
            raise ValidationError(
                "The specified job is already running or queued. "
                "Please wait for it to finish before starting a new one."
            )

        # If the DB import has any other status than accepted, i.e. it was started at least once and
        # was imported or did not finish for any reason do not re-validate the job again
        if curr_job.status != JobStatus.ACCEPTED:
            raise ValidationError(
                "The db import of this job has been started. It cannot be re-validated again. "
                "Please create another batch request to import the entries."
            )

        curr_job.validation_status = JobStatus.STARTED
        curr_job.save()

        transaction.on_commit(
            lambda: batch_import.apply_async(
                (
                    str(import_job_id),
                    True,
                ),
                link_error=link_error_handler.s(),
                ignore_result=True,
            )
        )

        return Response(status=status.HTTP_202_ACCEPTED)
