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
from backend.models.jobs import BaseJob, JobStatus
from backend.permissions import predicates


class ImportJobMode(models.TextChoices):
    SKIP_DUPLICATES = "skip_duplicates", _("Skip Duplicates")
    ALLOW_DUPLICATES = "allow_duplicates", _("Allow Duplicates")
    UPDATE = "update", _("Update")


class RowStatus(models.TextChoices):
    ERROR = "error", _("Error")
    INVALID = "invalid", _("Invalid")
    SKIP = "skip", _("Skip")
    NEW = "new", _("New")
    UPDATE = "update", _("Update")
    DELETE = "delete", _("Delete")


class ImportJobReport(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Import Job Report")
        verbose_name_plural = _("Import Job Reports")
        rules_permissions = {
            "view": predicates.is_at_least_editor_or_super,
            "add": predicates.is_at_least_editor_or_super,
            "change": predicates.is_at_least_editor_or_super,
            "delete": predicates.is_at_least_editor_or_super,
        }

    # From results
    new_rows = models.IntegerField(null=True)
    error_rows = models.IntegerField(null=True)
    update_rows = models.IntegerField(null=True)

    accepted_columns = ArrayField(
        models.CharField(max_length=DEFAULT_TITLE_LENGTH), blank=True, default=list
    )
    ignored_columns = ArrayField(
        models.CharField(max_length=DEFAULT_TITLE_LENGTH), blank=True, default=list
    )


class ImportJobReportRow(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Import Job Report Row")
        verbose_name_plural = _("Import Job Report Rows")
        rules_permissions = {
            "view": predicates.is_at_least_editor_or_super,
            "add": predicates.is_at_least_editor_or_super,
            "change": predicates.is_at_least_editor_or_super,
            "delete": predicates.is_at_least_editor_or_super,
        }

    report = models.ForeignKey(
        ImportJobReport, on_delete=models.CASCADE, related_name="rows"
    )

    status = models.CharField(max_length=7, choices=RowStatus.choices)
    errors = ArrayField(
        models.CharField(max_length=MAX_NOTE_LENGTH), blank=True, default=list
    )

    row_number = models.IntegerField()

    identifier_field = models.CharField(max_length=DEFAULT_TITLE_LENGTH)
    identifier_value = models.CharField(max_length=DEFAULT_TITLE_LENGTH)


class ImportJob(BaseJob):
    class Meta:
        verbose_name = _("Import Job")
        verbose_name_plural = _("Import Jobs")
        rules_permissions = {
            "view": predicates.is_at_least_editor_or_super,
            "add": predicates.is_at_least_editor_or_super,
            "change": predicates.is_at_least_editor_or_super,
            "delete": predicates.is_at_least_editor_or_super,
        }

    title = models.CharField(blank=True, max_length=MAX_DESCRIPTION_LENGTH)

    mode = models.CharField(
        choices=ImportJobMode.choices,
        max_length=16,
        default=ImportJobMode.SKIP_DUPLICATES,
    )

    run_as_user = models.ForeignKey(
        get_user_model(), blank=True, null=True, on_delete=models.PROTECT
    )

    data = models.ForeignKey("backend.File", null=True, on_delete=models.SET_NULL)

    # overriding BaseJob
    status = models.CharField(
        max_length=9,
        choices=JobStatus.choices,
        null=True,
        blank=True,
        default=None,
    )

    # The following fields are for the dry-run and then presenting those results
    validation_task_id = models.CharField(max_length=255, null=True, blank=True)

    validation_status = models.CharField(
        max_length=9,
        choices=JobStatus.choices,
        null=True,
        blank=True,
        default=None,
    )

    validation_report = models.OneToOneField(
        ImportJobReport, null=True, on_delete=models.SET_NULL
    )

    failed_rows_csv = models.ForeignKey(
        "backend.File",
        null=True,
        on_delete=models.SET_NULL,
        related_name="import_job_failed_rows_csv_set",
    )

    def _delete_report(self):
        import_job_report = self.validation_report
        if import_job_report:
            import_job_report.delete()

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
