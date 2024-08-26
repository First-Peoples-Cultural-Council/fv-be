from django.db import models
from django.utils.translation import gettext as _

from backend.models.jobs import BaseJob
from backend.permissions import predicates


class MTDExportFormat(BaseJob):
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

    export_result = models.JSONField(default=dict)

    def __str__(self):
        return self.site.title + " - MTD Export - " + str(self.id)
