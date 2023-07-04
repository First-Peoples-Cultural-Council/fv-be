from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseModel
from backend.permissions import predicates


class UserProfile(BaseModel):
    """
    Extra user information. Currently only used to hold information migrated from the old server.
    """

    class Meta:
        verbose_name = _("user profile")
        verbose_name_plural = _("user profiles")
        rules_permissions = {
            "view": predicates.can_view_user_info,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # matched based on userinfo:email
    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name="profile"
    )

    # from fvuserinfo:traditionalName
    traditional_name = models.CharField(max_length=300, blank=True)

    # from fvuserinfo:preferences
    preferences = models.CharField(max_length=500, blank=True)

    # from fvuserinfo:ip
    ip = models.CharField(max_length=64, blank=True)

    # from fvuserinfo:ua
    ua = models.CharField(max_length=200, blank=True)

    # from fvuserinfo:referer
    referer = models.CharField(max_length=300, blank=True)

    # created / last_modified fields have no past equivalent and will be set on import
