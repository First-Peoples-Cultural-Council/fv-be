from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext as _

from backend.models.async_results import BaseJob
from backend.models.base import BaseSiteContentModel
from backend.models.constants import DEFAULT_TITLE_LENGTH, MAX_NOTE_LENGTH
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
    total_rows = models.IntegerField(null=True)
    column_headers = ArrayField(
        models.CharField(max_length=DEFAULT_TITLE_LENGTH), blank=True, default=list
    )
    totals = models.JSONField(
        null=True
    )  # todo: probably save the numbers we care about in named fields instead


class ImportJobReportRow(BaseSiteContentModel):
    report = models.ForeignKey(
        ImportJobReport, on_delete=models.CASCADE, related_name="rows"
    )

    status = models.CharField(max_length=7, choices=RowStatus.choices)
    errors = ArrayField(
        models.CharField(max_length=MAX_NOTE_LENGTH), blank=True, default=list
    )

    row_number = models.IntegerField()
    identifier_field = models.CharField(
        max_length=DEFAULT_TITLE_LENGTH
    )  # todo: this can be shorter
    identifier_value = models.CharField(max_length=DEFAULT_TITLE_LENGTH)

    # todo: link to the created object (probably via a model-specific m2m table?)


class ImportJob(BaseJob):
    class Meta:
        verbose_name = _("Import Job")
        verbose_name_plural = _("Import Jobs")
        rules_permissions = {
            "view": predicates.is_language_admin_or_super,
            "add": predicates.is_language_admin_or_super,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_language_admin_or_super,
        }

    title = models.CharField(blank=True)

    mode = models.CharField(
        choices=ImportJobMode.choices,
        max_length=16,
        default=ImportJobMode.SKIP_DUPLICATES,
    )

    run_as_user = models.ForeignKey(
        get_user_model(), blank=True, null=True, on_delete=models.PROTECT
    )

    data = models.OneToOneField(File, null=True, on_delete=models.SET_NULL)

    # todo: does the validation_result need to include all rows or only the ones with messages?
    validation_report = models.OneToOneField(
        ImportJobReport, null=True, on_delete=models.SET_NULL
    )

    # todo: import_report = models.OneToOneField(
    #         ImportJobReport, null=True, on_delete=models.SET_NULL
    #     )
