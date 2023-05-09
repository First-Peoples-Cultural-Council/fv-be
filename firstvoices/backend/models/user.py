from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.managers.user import UserManager


class User(AbstractUser):
    """
    User Model
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

    email = models.EmailField(unique=True, null=False, default="test@test.com")

    password = models.CharField(null=True, blank=False, max_length=128)

    is_staff = models.BooleanField(null=False, default=False)
    is_superuser = models.BooleanField(null=False, default=False)

    @property
    def first_name(self):
        return None

    @property
    def last_name(self):
        return None

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def username(self):
        return self.id

    @property
    def is_authenticated(self):
        return True

    @property
    def groups(self):
        return None

    def __str__(self):
        return str(self.id)

    @property
    def natural_key(self):
        return (self.id,)

    class Meta:
        db_table = "user"
