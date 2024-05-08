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
from backend.models.media import File
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
    skipped_rows = models.IntegerField(null=True)
    error_rows = models.IntegerField(null=True)

    column_headers = ArrayField(
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

    # Unused for MVP, can be removed and be added back later if required
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

    data = models.OneToOneField(File, null=True, on_delete=models.SET_NULL)

    # The following fields are for the dry-run and then presenting those results
    validation_task_id = models.CharField(max_length=255, null=True, blank=True)

    validation_status = models.CharField(
        max_length=9,
        choices=JobStatus.choices,
        default=JobStatus.ACCEPTED,
    )

    validation_report = models.OneToOneField(
        ImportJobReport, null=True, on_delete=models.SET_NULL
    )
