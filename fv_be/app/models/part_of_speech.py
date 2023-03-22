from django.db import models
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

# FirstVoices
from .base import BaseModel


class PartOfSpeech(BaseModel):
    """Model for Parts Of Speech."""

    # Fields
    title = models.CharField(max_length=200)
    # i.e. A PartOfSpeech may have a parent, but the parent PartOfSpeech cannot have a parent itself.
    # (i.e. no grandparents). This is enforced in the clean method.
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")

    class Meta:
        verbose_name = _("PartOfSpeech")
        verbose_name_plural = _("PartsOfSpeech")

    def __str__(self):
        return self.title

    def clean(self):
        self.is_cleaned = True
        # Enforce only one max level of nesting
        parent_part_of_speech = self.parent
        if parent_part_of_speech and parent_part_of_speech.parent:
            raise ValidationError(
                _("A PartOfSpeech may have a parent, but the parent PartOfSpeech cannot have a "
                  "parent itself. (i.e. no grandparents)")
            )
        super().clean()

    def save(self, *args, **kwargs):
        if not self.is_cleaned:
            self.full_clean()
        super().save(*args, **kwargs)
