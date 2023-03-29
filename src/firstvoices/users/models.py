from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """
    User Model
    """

    # todo: tbd how to handle username, id, and email fields to support both cognito and the admin site, FW-4165
    # todo: decide how to handle group field, FW-4165

    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = ["username"]

    """
    Maps to JWT 'sub' field -- this is the primary key
    """
    id = models.CharField(max_length=64, primary_key=True)

    username = models.CharField(max_length=64, blank=True, null=True, unique=True)

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return str(self.id)

    def natural_key(self):
        return (self.id,)

    def get_absolute_url(self):
        """Get url for user's detail view.
        Returns:
            str: URL for user detail.
        """
        return reverse("users:detail", kwargs={"username": self.username})

    class Meta:
        db_table = "user"
