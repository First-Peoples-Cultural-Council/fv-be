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
    # i.e. Parent Categories can have children but those children cannot have more children
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.title

    def clean(self):
        self.is_cleaned = True
        # Enforce only one max level of nesting
        parent_category = self.parent
        if parent_category and parent_category.parent:
            raise ValidationError(
                _("Choosing categories that are themselves children of other categories is not allowed.")
            )
        super().clean()

    def save(self, *args, **kwargs):
        if not self.is_cleaned:
            self.full_clean()
        super().save(*args, **kwargs)
