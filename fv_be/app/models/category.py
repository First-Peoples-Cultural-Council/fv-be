from django.db import models
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

# FirstVoices
from .sites import BaseSiteContentModel


class Category(BaseSiteContentModel):
    """Model for Categories."""

    # Fields
    title = models.CharField(max_length=200)
    description = models.TextField()
    # i.e. A category may have a parent, but the parent category cannot have a parent itself. (i.e. no grandparents).
    # This is enforced in the clean method.
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.PROTECT, related_name="children")

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.title

    def clean(self):
        self.is_cleaned = True
        # Enforce only one max level of nesting
        parent_category = self.parent
        if parent_category and parent_category.parent:
            raise ValidationError(
                _("A category may have a parent, but the parent category cannot have a parent itself. " +
                  "(i.e. no grandparents)")
            )
        super().clean()

    def save(self, *args, **kwargs):
        if not self.is_cleaned:
            self.full_clean()
        super().save(*args, **kwargs)
