from django.db import models
from django.utils.translation import gettext as _

# FirstVoices
from .base import BaseModel


class PartOfSpeech(BaseModel):
    """Model for Parts Of Speech."""

    # Fields
    title = models.CharField(max_length=200)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")

    class Meta:
        verbose_name = _("PartOfSpeech")
        verbose_name_plural = _("PartsOfSpeech")

    def __str__(self):
        return self.name
