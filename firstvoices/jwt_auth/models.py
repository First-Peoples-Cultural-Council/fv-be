from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """
    User Model.

    A Django user model customized for token authentication:
        * id is an immutable db key
        * email is a required, unique field, so it can be treated like a username
        * sub is a non-required field that holds the unique JWT "sub" (subject) field for token authentication
        * password is not required

    Notes:
        * is_staff and is_superuser are included, only because they are used by the admin site

    """

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    id = models.BigAutoField(primary_key=True)

    # set in authentication.JwtAuthentication.authenticate
    sub = models.CharField(max_length=64, blank=True, unique=True, null=True)

    email = models.EmailField(unique=True, null=False)

    password = models.CharField(null=True, blank=False, max_length=128)

    @property
    def username(self):
        return self.id

    def __str__(self):
        return str(self.email)

    @property
    def natural_key(self):
        return (self.email,)

    class Meta:
        db_table = "user"
