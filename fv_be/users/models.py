import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model for FirstVoices Backend. Uses email as the username, and adds a separate id as the primary
    key to allow for users changing their email address.
    """

    # remove unused inherited fields
    username = None
    first_name = None
    last_name = None

    # todo: this is a new id, should it be a uid like the others or a bigint instead?
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )

    # from email
    # todo: verify whether user can log in before they verify their email address
    email = models.EmailField(_("email address"), blank=False, unique=True)
    USERNAME_FIELD = email
    EMAIL_FIELD = email
    REQUIRED_FIELDS = ["display_name", "full_name"]

    # The short name, e.g., for greeting the user
    # from first_name
    display_name = models.CharField(
        max_length=30, blank=False, verbose_name="Display Name"
    )

    # The full name of the user, mainly used for searching. This is a single field to be inclusive.
    # from firstName lastName | traditionalName
    full_name = models.CharField(max_length=300, blank=False, verbose_name="Full Name")

    # note: appropriate min and max values for this change as time passes, so validation needs to happen in code as well
    year_born = models.IntegerField(blank=True, null=True)

    # from dc:creator
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # todo: is this good?
        default=None,
        related_name="created_%(app_label)s_%(class)s",
    )

    # from dc:created
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    # from dc:modified
    last_modified_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # todo: is this good?
        default=None,
        related_name="modified_%(app_label)s_%(class)s",
    )

    # from dc:lastContributor
    last_modified = models.DateTimeField(auto_now=True, db_index=True)

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"id": self.id})
