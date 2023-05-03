from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext as _

from backend.permissions import predicates

from .base import BaseModel
from .constants import AppRole


class AppJson(BaseModel):
    """
    Represents named values not associated with a specific site, such as default content values.
    """

    key = models.CharField(max_length=25, unique=True)
    json = models.JSONField()

    class Meta:
        verbose_name = _("backend json value")
        verbose_name_plural = _("backend json values")

    def __str__(self):
        return self.key


class AppMembership(BaseModel):
    """
    Represents app-level memberships that apply across all sites, such as staff admins.
    """

    # from user
    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name="app_role"
    )

    # from group memberships
    role = models.IntegerField(choices=AppRole.choices, default=AppRole.STAFF)

    class Meta:
        verbose_name = _("app-level membership")
        verbose_name_plural = _("app-level memberships")
        rules_permissions = {
            "view": predicates.is_at_least_staff_admin,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    def __str__(self):
        return f"{self.user} ({self.get_role_display()})"
