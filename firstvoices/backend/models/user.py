from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _

from backend.managers.user import UserManager
from backend.models import BaseModel
from backend.permissions import predicates


class User(AbstractUser):
    """
    User Model.

    A Django user model customized for token authentication:
        * username/id is set up for the JWT "sub" (subject) field
        * email is a required, unique field, so it can be treated like a username
        * password is not required

    """

    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    """
    Maps to JWT 'sub' field -- this is the primary key
    """
    id = models.CharField(
        max_length=64, blank=False, unique=True, primary_key=True, null=False
    )

    # from userinfo:email
    email = models.EmailField(unique=True, null=False)

    password = models.CharField(null=True, blank=False, max_length=128)

    # last_name from userinfo:lastName
    # first_name from userinfo:firstName

    @property
    def username(self):
        return self.id

    def __str__(self):
        return str(self.email)

    @property
    def natural_key(self):
        return (self.id,)

    class Meta:
        db_table = "user"


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
