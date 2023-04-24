from django.db import models
from django.db.models import Model


class Role(Model):
    """
    Roles
    """

    name = models.CharField(
        max_length=64,
        unique=True,
    )

    description = models.CharField(
        max_length=255,
    )

    class Meta:
        db_table = "role"
