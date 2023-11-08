import rules
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseModel, BaseSiteContentModel
from backend.models.constants import MAX_REASON_NOTE_LENGTH
from backend.permissions import predicates


class JoinRequestStatus(models.IntegerChoices):
    # enum intentionally has gaps to allow future changes to keep sequential order
    CANCELLED = -30, _("Cancelled")
    REJECTED = -20, _("Rejected")  # notify user
    IGNORED = -10, _("Ignored")
    PENDING = 0, _("Pending")
    APPROVED = 10, _("Approved")  # notify user


class JoinRequestReasonChoices(models.IntegerChoices):
    # enum intentionally has gaps to allow future changes to keep sequential order
    OTHER = 10, _("Other")
    LANGUAGE_LEARNER = 20, _("Learning the language")
    LANGUAGE_TEACHER = 30, _("Teaching the language")
    FLUENT_SPEAKER = 40, _("Fluent speaker")
    LANGUAGE_INTEREST = 50, _("Interested in languages")
    HERITAGE = 60, _("Part of my heritage")
    COMMUNITY_MEMBER = 70, _("Member of this community/nation")
    COMMUNITY_STAFF = 80, _("Working with this community/nation")
    RECONCILIATION = 90, _("Reconciliation")
    FV_TEAM = 100, _("Part of this FirstVoices Language Team")


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

    reason_note = models.CharField(max_length=MAX_REASON_NOTE_LENGTH)

    def __str__(self):
        return f"Request from {self.user} to join {self.site}. Status: {self.status}"


class JoinRequestReason(BaseModel):
    """
    Represents a reason for joining a site.
    """

    class Meta:
        verbose_name = _("Join Request Reason")
        verbose_name_plural = _("Join Request Reasons")
        constraints = [
            models.UniqueConstraint(
                fields=["join_request", "reason"],
                name="unique_reasons_per_join_request",
            )
        ]
        rules_permissions = {
            "view": rules.always_allow,
            "add": rules.is_authenticated,
            "change": predicates.is_at_least_language_admin,
            "delete": predicates.is_at_least_language_admin,
        }

    join_request = models.ForeignKey(
        JoinRequest, on_delete=models.CASCADE, related_name="reasons_set"
    )
    reason = models.IntegerField(
        choices=JoinRequestReasonChoices.choices, default=JoinRequestReasonChoices.OTHER
    )

    def __str__(self):
        return self.get_reason_display()
