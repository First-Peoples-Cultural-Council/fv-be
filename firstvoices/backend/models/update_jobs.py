from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.models.constants import (
    DEFAULT_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_NOTE_LENGTH,
)
from backend.models.jobs import BaseJob
from backend.permissions import predicates


# Todo: Verify status copy
class UpdateJobStatus(models.TextChoices):
    ACCEPTED = "accepted", "Accepted"
    STARTED = "started", "Started"
    COMPLETE = "complete", "Complete"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"
    READY_FOR_IMPORT = "ready_for_import", "Ready for import"


class UpdateJobRowStatus(models.TextChoices):
    ERROR = "error", _("Error")
    INVALID = "invalid", _("Invalid")
    SKIP = "skip", _("Skip")
    NEW = "new", _("New")
    UPDATE = "update", _("Update")
    DELETE = "delete", _("Delete")


class UpdateJobReport(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Update Job Report")
        verbose_name_plural = _("Update Job Reports")
        rules_permissions = {
            "view": predicates.is_at_least_editor_or_super,
            "add": predicates.is_at_least_editor_or_super,
            "change": predicates.is_at_least_editor_or_super,
            "delete": predicates.is_at_least_editor_or_super,
        }

    # todo: Verify report rows structure
    # todo: e.g. do we need updated_rows now ?
    new_rows = models.IntegerField(null=True)
    error_rows = models.IntegerField(null=True)
    updated_rows = models.IntegerField(null=True)
    warnings = models.IntegerField(null=True)

    accepted_columns = ArrayField(
        models.CharField(max_length=DEFAULT_TITLE_LENGTH), blank=True, default=list
    )
    ignored_columns = ArrayField(
        models.CharField(max_length=DEFAULT_TITLE_LENGTH), blank=True, default=list
    )


class UpdateJobReportRow(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Update Job Report Row")
        verbose_name_plural = _("Update Job Report Rows")
        rules_permissions = {
            "view": predicates.is_at_least_editor_or_super,
            "add": predicates.is_at_least_editor_or_super,
            "change": predicates.is_at_least_editor_or_super,
            "delete": predicates.is_at_least_editor_or_super,
        }

    report = models.ForeignKey(
        UpdateJobReport, on_delete=models.CASCADE, related_name="rows"
    )

    status = models.CharField(max_length=7, choices=UpdateJobRowStatus.choices)
    errors = ArrayField(
        models.CharField(max_length=MAX_NOTE_LENGTH), blank=True, default=list
    )

    row_number = models.IntegerField()

    identifier_field = models.CharField(max_length=DEFAULT_TITLE_LENGTH)
    identifier_value = models.CharField(max_length=DEFAULT_TITLE_LENGTH)


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

    status = models.CharField(
        max_length=32,
        choices=UpdateJobStatus.choices,
        null=True,
        blank=True,
        default=None,
    )

    validation_task_id = models.CharField(max_length=255, null=True, blank=True)

    validation_status = models.CharField(
        max_length=32,
        choices=UpdateJobStatus.choices,
        null=True,
        blank=True,
        default=None,
    )

    validation_report = models.OneToOneField(
        UpdateJobReport, null=True, on_delete=models.SET_NULL
    )

    failed_rows_csv = models.ForeignKey(
        "backend.File",
        null=True,
        on_delete=models.SET_NULL,
        related_name="update_job_failed_rows_csv_set",
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
        file = apps.get_model("backend", "File")
        image_file = apps.get_model("backend", "ImageFile")
        video_file = apps.get_model("backend", "VideoFile")

        images = image_file.objects.filter(update_job_id=self.id)
        videos = video_file.objects.filter(update_job_id=self.id)
        audio = file.objects.filter(update_job_id=self.id)

        if images.exists():
            images.delete()
        if videos.exists():
            videos.delete()
        if audio.exists():
            audio.delete()

    def delete(self, using=None, keep_parents=False):
        self._delete_report()
        self._delete_failed_rows_csv()
        self._delete_data_csv()
        self._delete_uploaded_media()
        return super().delete(using, keep_parents)
