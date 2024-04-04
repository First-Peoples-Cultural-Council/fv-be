from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.permissions import predicates


class JobStatus(models.TextChoices):
    # Choices for Type
    ACCEPTED = "accepted", _("Accepted")
    STARTED = "started", _("Started")
    COMPLETE = "complete", _("Complete")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")


class BaseJob(BaseSiteContentModel):
    """Base model for tracking asynchronous jobs, such as batch processing."""

    class Meta:
        abstract = True

    task_id = models.CharField(max_length=255, null=True, blank=True)

    status = models.CharField(
        max_length=6,
        choices=JobStatus.choices,
        default=JobStatus.ACCEPTED,
    )


class CustomOrderRecalculationResult(BaseSiteContentModel):
    """Model to store custom order recalculation results."""

    class Meta:
        verbose_name = _("custom order recalculation result")
        verbose_name_plural = _("custom order recalculation results")
        rules_permissions = {
            "view": predicates.is_superadmin,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

        indexes = [
            models.Index(fields=["site", "is_preview"], name="corr_site_preview_idx"),
        ]

    latest_recalculation_date = models.DateTimeField(auto_now_add=True)
    latest_recalculation_result = models.JSONField()
    task_id = models.CharField(max_length=255, null=True, blank=True)
    is_preview = models.BooleanField(default=True)

    def __str__(self):
        return self.site.title + " - " + str(self.latest_recalculation_date)
