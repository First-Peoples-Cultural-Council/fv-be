from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.managers.user import UserManager


class User(AbstractUser):
    """
    User Model.

    A Django user model customized for token authentication:
        * username/id is set up for the JWT "sub" (subject) field
        * email is a required, unique field, so it can be treated like a username
        * password is not required
        * name fields are not stored, so we can depend on jwt id tokens instead

    Notes:
        * is_staff and is_superuser are included, only because they are used by the admin site

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

    @property
    def first_name(self):
        return ""

    @property
    def last_name(self):
        return ""

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
