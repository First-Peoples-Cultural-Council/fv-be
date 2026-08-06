from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext as _

from backend.models.batch_job_utils import BatchJobReport
from backend.models.constants import MAX_DESCRIPTION_LENGTH
from backend.models.jobs import BaseJob
from backend.permissions import predicates


class UpdateJobStatus(models.TextChoices):
    # From BaseJob.JobStatus
    ACCEPTED = "accepted", "Accepted"
    STARTED = "started", "Started"
    COMPLETE = "complete", "Complete"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    READY_FOR_UPDATE = "ready_for_update", "Ready for update"


class UpdateJob(BaseJob):
    class Meta:
        verbose_name = _("Update Job")
        verbose_name_plural = _("Update Jobs")
        rules_permissions = {
            "view": predicates.is_at_least_editor_or_super,
            "add": predicates.is_at_least_editor_or_super,
            "change": predicates.is_at_least_editor_or_super,
            "delete": predicates.is_at_least_editor_or_super,
        }

    title = models.CharField(blank=True, max_length=MAX_DESCRIPTION_LENGTH)

    run_as_user = models.ForeignKey(
        get_user_model(), blank=True, null=True, on_delete=models.PROTECT
    )

    data = models.ForeignKey("backend.File", null=True, on_delete=models.SET_NULL)

    # overriding BaseJob
    status = models.CharField(
        max_length=32,
        choices=UpdateJobStatus.choices,
        null=True,
        blank=True,
        default=None,
    )

    # The following fields are for the dry-run and then presenting those results
    validation_task_id = models.CharField(max_length=255, null=True, blank=True)

    validation_status = models.CharField(
        max_length=32,
        choices=UpdateJobStatus.choices,
        null=True,
        blank=True,
        default=None,
    )

    validation_report = models.OneToOneField(
        BatchJobReport, null=True, on_delete=models.SET_NULL
    )

    failed_rows_csv = models.ForeignKey(
        "backend.File",
        null=True,
        on_delete=models.SET_NULL,
        related_name="import_job_failed_rows_csv_set",
    )

    def _delete_report(self):
        update_job_report = self.validation_report
        if update_job_report:
            update_job_report.delete()

    def _delete_data_csv(self):
        data_csv = self.data
        if data_csv:
            data_csv.delete()

    def _delete_failed_rows_csv(self):
        failed_rows_csv = self.failed_rows_csv
        if failed_rows_csv:
            failed_rows_csv.delete()

    def _delete_uploaded_media(self):
        # Use the apps.get_model() method to avoid circular imports
        file = apps.get_model("backend", "File")
        image_file = apps.get_model("backend", "ImageFile")
        video_file = apps.get_model("backend", "VideoFile")

        images = image_file.objects.filter(import_job_id=self.id)
        videos = video_file.objects.filter(import_job_id=self.id)
        audio = file.objects.filter(import_job_id=self.id)

        if images.exists():
            images.delete()
        if videos.exists():
            videos.delete()
        if audio.exists():
            audio.delete()

    def delete(self, using=None, keep_parents=False):
        """
        Cleans up the import job by deleting the associated files and reports.
        """

        self._delete_report()
        self._delete_failed_rows_csv()
        self._delete_data_csv()
        self._delete_uploaded_media()
        return super().delete(using, keep_parents)
