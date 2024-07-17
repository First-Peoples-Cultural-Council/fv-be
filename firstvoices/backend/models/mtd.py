from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.permissions import predicates


class MTDExportFormat(BaseSiteContentModel):
    """Model to store MTD app export format results.
    This format includes the configuration, inverted indices,
    and entry scoring needed by an MTD compatible front-end.
    """

    class Meta:
        verbose_name = _("Mother Tongues dictionary export format result")
        verbose_name_plural = _("Mother Tongues dictionary export format results")
        get_latest_by = "created"
        rules_permissions = {
            "view": predicates.is_superadmin,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

        indexes = [
            models.Index(fields=["site", "is_preview"], name="mtd_site_preview_idx"),
        ]

    latest_export_result = models.JSONField(default=dict)
    task_id = models.CharField(max_length=255, null=True, blank=True)
    is_preview = models.BooleanField(default=True)

    def __str__(self):
        return self.site.title + " - " + str(self.latest_export_date)
