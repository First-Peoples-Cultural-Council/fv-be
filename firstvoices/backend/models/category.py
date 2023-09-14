from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.models.constants import CATEGORY_POS_MAX_TITLE_LENGTH
from backend.permissions import predicates


class Category(BaseSiteContentModel):
    """Model for Categories."""

    # Fields
    title = models.CharField(max_length=CATEGORY_POS_MAX_TITLE_LENGTH)
    description = models.TextField(blank=True)
    # i.e. A category may have a parent, but the parent category cannot have a parent itself. (i.e. no grandparents).
    # This is enforced in the clean method.
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        unique_together = ("site", "title")
        ordering = ["title"]
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_language_admin_or_super,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_language_admin_or_super,
        }

        indexes = [
            models.Index(fields=["title", "site"], name="category_site_title_idx"),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        self.is_cleaned = True
        # Enforce only one max level of nesting
        parent_category = self.parent
        if parent_category and parent_category.parent:
            raise ValidationError(
                _(
                    "A category may have a parent, but the parent category cannot have a parent itself. "
                    + "(i.e. no grandparents)"
                )
            )
        super().clean()

    def save(self, *args, **kwargs):
        if not hasattr(self, "is_cleaned"):
            self.is_cleaned = False
        if not self.is_cleaned:
            self.full_clean()
        super().save(*args, **kwargs)
