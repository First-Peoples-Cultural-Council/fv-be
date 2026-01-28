from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.models.constants import Visibility
from backend.permissions import predicates


class JobStatus(models.TextChoices):
    # Choices for Type
    ACCEPTED = "accepted", _("Accepted")
    STARTED = "started", _("Started")
    COMPLETE = "complete", _("Complete")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")
    EXPIRED = "expired", _("Expired")


class BaseJob(BaseSiteContentModel):
    """Base model for tracking asynchronous jobs, such as batch processing."""

    class Meta:
        abstract = True

    task_id = models.CharField(max_length=255, null=True, blank=True)

    status = models.CharField(
        max_length=9,
        choices=JobStatus.choices,
        default=JobStatus.ACCEPTED,
    )

    # an error message if the job was cancelled
    message = models.TextField(blank=True, null=True)


class DictionaryCleanupJob(BaseJob):
    """Model to store dictionary cleanup results."""

    class Meta:
        verbose_name = _("dictionary cleanup job")
        verbose_name_plural = _("dictionary cleanup jobs")
        rules_permissions = {
            "view": predicates.is_superadmin,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

        indexes = [
            models.Index(fields=["site", "is_preview"], name="corr_site_preview_idx"),
        ]

    cleanup_result = models.JSONField(blank=True, null=True)
    is_preview = models.BooleanField(default=True)

    def __str__(self):
        return self.site.title + " - DictionaryCleanup - " + str(self.id)


class BulkVisibilityJob(BaseJob):
    """Model to store job results for bulk visibility changes."""

    class Meta:
        verbose_name = _("bulk visibility job")
        verbose_name_plural = _("bulk visibility jobs")
        rules_permissions = {
            "view": predicates.is_superadmin,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    from_visibility = models.IntegerField(
        choices=Visibility.choices, default=Visibility.TEAM
    )

    to_visibility = models.IntegerField(
        choices=Visibility.choices, default=Visibility.TEAM
    )

    def __str__(self):
        return self.site.title + " - BulkVisibility - " + self.status


class ExportJob(BaseJob):
    class Meta:
        verbose_name = _("Export Job")
        verbose_name_plural = _("Export Jobs")
        rules_permissions = {
            "view": predicates.is_at_least_assistant_or_super,
            "add": predicates.is_at_least_assistant_or_super,
            "change": predicates.is_at_least_assistant_or_super,
            "delete": predicates.is_at_least_assistant_or_super,
        }

    export_csv = models.ForeignKey(
        "backend.File",
        null=True,
        on_delete=models.SET_NULL,
        related_name="export_job_export_csv_set",
    )

    def __str__(self):
        return f"{self.site.title} Export Job (id: {str(self.id)})"
