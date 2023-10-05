from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.models.constants import JoinRequestStatus
from backend.permissions import predicates


class JoinRequest(BaseSiteContentModel):
    """
    Represents a request to join a site. This is used to track the status of the request.
    """

    class Meta:
        verbose_name = _("Join Request")
        verbose_name_plural = _("Join Requests")
        constraints = [
            models.UniqueConstraint(
                fields=["site", "user"], name="unique_site_user_join_request"
            )
        ]
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_language_admin_or_super,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_language_admin_or_super,
        }

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="join_requests"
    )

    status = models.IntegerField(
        choices=JoinRequestStatus.choices, default=JoinRequestStatus.PENDING
    )

    def __str__(self):
        return f"Request from {self.user} to join {self.site}. Status: {self.status}"
