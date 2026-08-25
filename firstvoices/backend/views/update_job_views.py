from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import parsers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.import_jobs import ImportJob, ImportJobMode, ImportJobStatus
from backend.serializers.import_job_serializers import ImportJobSerializer
from backend.serializers.update_job_serializers import (
    UpdateJobDetailSerializer,
    UpdateJobSerializer,
)
from backend.tasks.batch_utils import verify_no_other_import_jobs_running
from backend.tasks.update_job_tasks import confirm_update_job, validate_update_job
from backend.tasks.utils.update_job_utils import verify_update_job_size_limit
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import (
    AsyncJobDeleteMixin,
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
)
from backend.views.import_update_job_view_helpers import notify_job_ready
from firstvoices.celery import link_error_handler

SUPPORT_USER_EMAIL = settings.SUPPORT_USER_EMAIL


@extend_schema_view(
    list=extend_schema(
        description=_(
            "A list of batch edit jobs associated with the specified site. "
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
        description=_("Details about a specific batch edit job."),
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
            "Creates a new batch edit job. The job can be validated or confirmed using the relevant endpoints."
        ),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201,
                response=ImportJobSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    destroy=extend_schema(
        description=_(
            "Deletes a single edit job and its associated file and result for the specified site. "
            "This action does not delete any of the entries edited by the job."
        ),
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
            "Confirm and start processing a previously validated batch edit job. "
            "This action will make changes to the dictionary, so it should be used with caution. "
            "In order to succeed, the validationStatus must already be 'COMPLETE' and there must be no other update "
            "jobs in progress for the site. When finished, the status will be 'COMPLETE'."
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
            "Validate a newly created batch edit job. "
            "This action checks the uploaded file for errors. "
            "No changes are made to the dictionary during validation, and the job must be confirmed separately."
        ),
        responses={
            202: OpenApiResponse(
                description=doc_strings.success_202_job_accepted,
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
class UpdateJobViewSet(
    AsyncJobDeleteMixin, SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    serializer_class = UpdateJobSerializer
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
        "notify": "change",
    }

    started_statuses = [
        ImportJobStatus.ACCEPTED,
        ImportJobStatus.STARTED,
        ImportJobStatus.COMPLETE,
    ]

    started_validation_statuses = [
        ImportJobStatus.ACCEPTED,
        ImportJobStatus.STARTED,
    ]

    def get_queryset(self):
        site = self.get_validated_site()
        return ImportJob.objects.filter(site=site, mode=ImportJobMode.UPDATE).order_by(
            "-created"
        )  # permissions are applied by the base view

    def perform_create(self, serializer):
        serializer.save(mode=ImportJobMode.UPDATE)
        verify_update_job_size_limit(serializer.instance)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UpdateJobDetailSerializer
        return UpdateJobSerializer

    @action(detail=True, methods=["post"])
    def validate(self, request, site_slug=None, pk=None):
        """
        Method to start the validation process on a given update-job.
        """
        import_job_id = self.kwargs["pk"]
        curr_job = ImportJob.objects.get(id=import_job_id, mode=ImportJobMode.UPDATE)

        # Checks to ensure consistency

        # Verify the current job is not running or queued.
        if curr_job.validation_status in self.started_validation_statuses:
            raise ValidationError(
                "This job has already been queued and is currently being validated."
            )

        if curr_job.status in self.started_statuses:
            raise ValidationError(
                "This job has already been confirmed and is currently being processed."
            )

        verify_no_other_import_jobs_running(curr_job)
        verify_update_job_size_limit(curr_job)

        # Queue the job for validation
        curr_job.validation_status = ImportJobStatus.ACCEPTED
        curr_job.save()

        transaction.on_commit(
            lambda: validate_update_job.apply_async(
                (str(import_job_id),),
                link_error=link_error_handler.s(),
                ignore_result=True,
            )
        )

        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def confirm(self, request, site_slug=None, pk=None):
        import_job_id = self.kwargs["pk"]

        curr_job = ImportJob.objects.get(id=import_job_id, mode=ImportJobMode.UPDATE)

        if curr_job.validation_status != ImportJobStatus.COMPLETE:
            raise ValidationError(
                "Please validate the job before confirming the update job."
            )

        if curr_job.status in [ImportJobStatus.ACCEPTED, ImportJobStatus.STARTED]:
            raise ValidationError(
                "This job has already been confirmed and is currently being processed."
            )

        if curr_job.status == ImportJobStatus.COMPLETE:
            raise ValidationError("This job has already finished processing.")

        verify_no_other_import_jobs_running(curr_job)
        verify_update_job_size_limit(curr_job)

        # Queue the job for confirmation
        curr_job.status = ImportJobStatus.ACCEPTED
        curr_job.save()

        transaction.on_commit(
            lambda: confirm_update_job.apply_async(
                (str(import_job_id),),
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

    @action(detail=True, methods=["post"])
    def notify(self, request, site_slug=None, pk=None):

        import_job_id = self.kwargs["pk"]
        return notify_job_ready(
            request=request,
            site_slug=site_slug,
            job_id=import_job_id,
            detail_view_name="api:updatejob-detail",
            already_ready_message="The update job is already marked ready for processing.",
            requires_validation_message="Please validate the job before marking it ready for processing.",
            subject="FirstVoices Batch Update Job ready",
            message_template=(
                "The following team has a batch update job ready to be processed.\n"
                "Site slug: {site_slug}\n"
                "UpdateJob id: {job_id}\n"
                "Requested by: {requester_email}\n"
                "URL: {url}\n"
            ),
            support_user_email=SUPPORT_USER_EMAIL,
        )
