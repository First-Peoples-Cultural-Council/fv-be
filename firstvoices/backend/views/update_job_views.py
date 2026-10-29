from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import parsers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.jobs import JobStatus
from backend.models.update_jobs import RollbackJob, UpdateJob, UpdateJobStatus
from backend.serializers.update_job_serializers import (
    RollbackJobSerializer,
    UpdateJobDetailSerializer,
    UpdateJobSerializer,
)
from backend.tasks.batch_utils import (
    verify_no_other_jobs_running,
    verify_no_other_update_jobs_running,
)
from backend.tasks.rollback_job_tasks import rollback_update_job
from backend.tasks.update_job_tasks import confirm_update_job, validate_update_job
from backend.tasks.utils.update_job_utils import verify_update_job_size_limit
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import (
    AsyncJobDeleteMixin,
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
)
from backend.views.import_update_job_view_helpers import (
    get_import_update_job_schema_view_config,
    notify_job_ready,
)
from firstvoices.celery import link_error_handler

SUPPORT_USER_EMAIL = settings.SUPPORT_USER_EMAIL


@extend_schema_view(
    **get_import_update_job_schema_view_config(
        serializer=UpdateJobSerializer,
        site_slug_parameter=site_slug_parameter,
        id_parameter=id_parameter,
        list_description=_(
            "A list of batch edit jobs associated with the specified site. "
            "See the detail view for more information on specified fields."
        ),
        retrieve_description=_("Details about a specific batch edit job."),
        create_description=_(
            "Creates a new batch edit job. The job can be validated or confirmed using the relevant endpoints."
        ),
        destroy_description=_(
            "Deletes a single edit job and its associated file and result for the specified site. "
            "This action does not delete any of the entries edited by the job."
        ),
        confirm_description=_(
            "Confirm and start processing a previously validated batch edit job. "
            "This action will make changes to the dictionary, so it should be used with caution. "
            "In order to succeed, the validationStatus must already be 'COMPLETE' and there must be no other update "
            "jobs in progress for the site. When finished, the status will be 'COMPLETE'."
        ),
        validate_description=_(
            "Validate a newly created batch edit job. "
            "This action checks the uploaded file for errors. "
            "No changes are made to the dictionary during validation, and the job must be confirmed separately."
        ),
        notify_description=_(
            "Marks a validated batch edit job as ready for processing and notifies support."
        ),
    ),
    rollback=[
        extend_schema(
            parameters=[site_slug_parameter, id_parameter],
            methods=["GET"],
            responses={200: RollbackJobSerializer},
            description=_(
                "Staff only. Retrieve the rollback status, conflicts, and errors."
            ),
        ),
        extend_schema(
            parameters=[site_slug_parameter, id_parameter],
            methods=["POST"],
            description=_(
                "Staff only. Queue rollback of a completed update job within seven days. "
                "Conflicts are reported and overridden."
            ),
            request=None,
            responses={202: RollbackJobSerializer},
        ),
    ],
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
        "rollback": "rollback",
    }

    started_statuses = [
        UpdateJobStatus.ACCEPTED,
        UpdateJobStatus.STARTED,
        UpdateJobStatus.COMPLETE,
        UpdateJobStatus.ROLLED_BACK,
    ]

    validating_statuses = [
        UpdateJobStatus.ACCEPTED,
        UpdateJobStatus.STARTED,
    ]

    def get_queryset(self):
        site = self.get_validated_site()
        return UpdateJob.objects.filter(site=site).order_by("-created")
        # permissions are applied by the base view

    def perform_create(self, serializer):
        serializer.save()
        verify_update_job_size_limit(serializer.instance)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UpdateJobDetailSerializer
        return UpdateJobSerializer

    @action(detail=True, methods=["post"])
    def validate(self, request, site_slug=None, pk=None):
        """
        Queue validation for a single update job.
        """
        update_job_id = self.kwargs["pk"]
        current_update_job = UpdateJob.objects.get(id=update_job_id)

        # Checks to ensure consistency

        # Verify the current job is not running or queued.
        if current_update_job.validation_status in self.validating_statuses:
            raise ValidationError(
                "This job has already been queued and is currently being validated."
            )

        if current_update_job.status in self.started_statuses:
            raise ValidationError(
                "This job has already been confirmed and is currently being processed."
            )

        verify_no_other_update_jobs_running(current_update_job)
        verify_update_job_size_limit(current_update_job)

        # Queue the job for validation
        current_update_job.validation_status = UpdateJobStatus.ACCEPTED
        current_update_job.save()

        transaction.on_commit(
            lambda: validate_update_job.apply_async(
                (str(update_job_id),),
                link_error=link_error_handler.s(),
                ignore_result=True,
            )
        )

        return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def confirm(self, request, site_slug=None, pk=None):
        """Queue execution for a previously validated update job."""
        update_job_id = self.kwargs["pk"]

        current_update_job = UpdateJob.objects.get(id=update_job_id)

        if current_update_job.validation_status != UpdateJobStatus.COMPLETE:
            raise ValidationError(
                "Please validate the job before confirming the update job."
            )

        if current_update_job.status in [
            UpdateJobStatus.ACCEPTED,
            UpdateJobStatus.STARTED,
        ]:
            raise ValidationError(
                "This job has already been confirmed and is currently being processed."
            )

        if current_update_job.status in [
            UpdateJobStatus.COMPLETE,
            UpdateJobStatus.ROLLED_BACK,
        ]:
            raise ValidationError("This job has already finished processing.")

        verify_no_other_update_jobs_running(current_update_job)
        verify_update_job_size_limit(current_update_job)

        # Queue the job for confirmation
        current_update_job.status = UpdateJobStatus.ACCEPTED
        current_update_job.save()

        transaction.on_commit(
            lambda: confirm_update_job.apply_async(
                (str(update_job_id),),
                link_error=link_error_handler.s(),
                ignore_result=True,
            )
        )

        return Response(status=status.HTTP_202_ACCEPTED)

    def perform_destroy(self, instance):
        if instance.validation_status in self.validating_statuses:
            raise ValidationError(
                f"This job cannot be deleted as it is being validated. "
                f"This job has the validation status: {instance.status}"
            )

        super().perform_destroy(instance)

    @action(detail=True, methods=["post"])
    def notify(self, request, site_slug=None, pk=None):
        """Mark a validated update job as ready for support processing."""

        update_job_id = self.kwargs["pk"]
        if self.get_object().status == UpdateJobStatus.ROLLED_BACK:
            raise ValidationError(
                "A rolled-back job cannot be marked ready for processing."
            )
        return notify_job_ready(
            request=request,
            site_slug=site_slug,
            job_id=update_job_id,
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
            job_model=UpdateJob,
            job_status_model=UpdateJobStatus,
        )

    @action(detail=True, methods=["get", "post"])
    def rollback(self, request, site_slug=None, pk=None):
        # TODO: Add orphan-only media/file/S3 deletion and cleanup-only retries.
        update_job = self.get_object()
        if request.method == "GET":
            rollback_job = get_object_or_404(RollbackJob, update_job=update_job)
            return Response(RollbackJobSerializer(rollback_job).data)

        # For POST requests, initiate the rollback process.
        # Ensure that the update job is eligible for rollback and that no other conflicting jobs are running.
        with transaction.atomic():
            update_job = UpdateJob.objects.get(id=pk, site=update_job.site)
            if (
                update_job.status != UpdateJobStatus.COMPLETE
                or update_job.change_snapshot is None
            ):
                raise ValidationError(
                    "Only completed jobs with snapshots can be rolled back."
                )
            if (
                update_job.rollback_expires_at is None
                or timezone.now() >= update_job.rollback_expires_at
            ):
                raise ValidationError("The seven-day rollback window has expired.")

            rollback_job, created = RollbackJob.objects.get_or_create(
                update_job=update_job,
                defaults={
                    "site": update_job.site,
                    "created_by": request.user,
                    "last_modified_by": request.user,
                },
            )
            if not created and rollback_job.status != JobStatus.FAILED:
                raise ValidationError("This rollback has already been requested.")
            verify_no_other_jobs_running(rollback_job)

            # If the rollback job already exists, reset its status and related fields for a new attempt.
            if not created:
                rollback_job.status = JobStatus.ACCEPTED
                rollback_job.message = None
                rollback_job.task_id = None
                rollback_job.conflicts = []
                rollback_job.last_modified_by = request.user
                rollback_job.save()
            transaction.on_commit(
                lambda: rollback_update_job.apply_async(
                    (str(rollback_job.id),),
                    link_error=link_error_handler.s(),
                    ignore_result=True,
                )
            )

        return Response(
            RollbackJobSerializer(rollback_job).data,
            status=status.HTTP_202_ACCEPTED,
        )
