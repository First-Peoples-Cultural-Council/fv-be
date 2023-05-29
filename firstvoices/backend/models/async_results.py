from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.permissions import predicates


class CustomOrderRecalculationPreviewResult(BaseSiteContentModel):
    """Model to store custom order recalculation preview results."""

    class Meta:
        verbose_name = _("custom order recalculation preview result")
        verbose_name_plural = _("custom order recalculation preview results")
        rules_permissions = {
            "view": predicates.is_superadmin,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    latest_recalculation_date = models.DateTimeField(auto_now_add=True)
    latest_recalculation_result = models.JSONField()
    task_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.site.title + " - " + str(self.date)
