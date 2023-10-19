import rules
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.models.constants import MAX_NOTE_LENGTH
from backend.permissions import predicates


class JoinRequestStatus(models.IntegerChoices):
    # enum intentionally has gaps to allow future changes to keep sequential order
    CANCELLED = -30, _("Cancelled")
    REJECTED = -20, _("Rejected")  # notify user
    IGNORED = -10, _("Ignored")
    PENDING = 0, _("Pending")
    APPROVED = 10, _("Approved")  # notify user


class JoinRequestReason(models.IntegerChoices):
    # enum intentionally has gaps to allow future changes to keep sequential order
    OTHER = 0, _("Other")
    LANGUAGE_LEARNER = 10, _("Learning the language")
    LANGUAGE_TEACHER = 20, _("Teaching the language")
    FLUENT_SPEAKER = 30, _("Fluent speaker")
    LANGUAGE_INTEREST = 40, _("Interested in languages")
    HERITAGE = 50, _("Part of my heritage")
    COMMUNITY_MEMBER = 60, _("Member of this community/nation")
    COMMUNITY_STAFF = 70, _("Working with this community/nation")
    RECONCILIATION = 80, _("Reconciliation")
    FV_TEAM = 90, _("Part of this FirstVoices Language Team")


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
            "view": predicates.is_at_least_language_admin,
            "add": rules.is_authenticated,
            "change": predicates.is_at_least_language_admin,
            "delete": predicates.is_at_least_language_admin,
        }
        indexes = [
            models.Index(fields=["site", "status"], name="join_request_status_idx"),
        ]

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="join_requests"
    )

    status = models.IntegerField(
        choices=JoinRequestStatus.choices, default=JoinRequestStatus.PENDING
    )

    # user will be able to add multiple reasons for joining, minimum of one
    reason = models.IntegerField(
        choices=JoinRequestReason.choices, default=JoinRequestReason.OTHER
    )

    reason_note = models.CharField(max_length=MAX_NOTE_LENGTH)

    def __str__(self):
        return f"Request from {self.user} to join {self.site}. Status: {self.status}"
