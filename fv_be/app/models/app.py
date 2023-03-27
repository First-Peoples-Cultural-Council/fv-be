from django.db import models
from django.utils.translation import gettext as _

from fv_be.app.models.base import BaseModel


class AppJson(BaseModel):
    """
    Represents named values not associated with a specific site, such as default content values.
    """

    key = models.CharField(max_length=25, unique=True)
    json = models.JSONField()

    class Meta:
        verbose_name = _("app json value")
        verbose_name_plural = _("app json values")

    def __str__(self):
        return self.key
