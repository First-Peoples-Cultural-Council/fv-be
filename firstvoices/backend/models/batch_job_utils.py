from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.models.constants import DEFAULT_TITLE_LENGTH, MAX_NOTE_LENGTH
from backend.permissions import predicates


class RowStatus(models.TextChoices):
    ERROR = "error", _("Error")
    INVALID = "invalid", _("Invalid")
    SKIP = "skip", _("Skip")
    NEW = "new", _("New")
    UPDATE = "update", _("Update")
    DELETE = "delete", _("Delete")


class BatchJobReport(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Batch Job Report")
        verbose_name_plural = _("Batch Job Reports")
        rules_permissions = {
            "view": predicates.is_at_least_editor_or_super,
            "add": predicates.is_at_least_editor_or_super,
            "change": predicates.is_at_least_editor_or_super,
            "delete": predicates.is_at_least_editor_or_super,
        }

    # From results
    new_rows = models.IntegerField(null=True)
    error_rows = models.IntegerField(null=True)
    updated_rows = models.IntegerField(null=True)

    accepted_columns = ArrayField(
        models.CharField(max_length=DEFAULT_TITLE_LENGTH), blank=True, default=list
    )
    ignored_columns = ArrayField(
        models.CharField(max_length=DEFAULT_TITLE_LENGTH), blank=True, default=list
    )


class BatchJobReportRow(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Batch Job Report Row")
        verbose_name_plural = _("Batch Job Report Rows")
        rules_permissions = {
            "view": predicates.is_at_least_editor_or_super,
            "add": predicates.is_at_least_editor_or_super,
            "change": predicates.is_at_least_editor_or_super,
            "delete": predicates.is_at_least_editor_or_super,
        }

    report = models.ForeignKey(
        BatchJobReport, on_delete=models.CASCADE, related_name="rows"
    )

    status = models.CharField(max_length=7, choices=RowStatus.choices)
    errors = ArrayField(
        models.CharField(max_length=MAX_NOTE_LENGTH), blank=True, default=list
    )

    row_number = models.IntegerField()

    identifier_field = models.CharField(max_length=DEFAULT_TITLE_LENGTH)
    identifier_value = models.CharField(max_length=DEFAULT_TITLE_LENGTH)
