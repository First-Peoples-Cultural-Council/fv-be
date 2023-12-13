from django.core.validators import validate_slug
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseControlledSiteContentModel
from backend.models.constants import DEFAULT_TITLE_LENGTH
from backend.permissions import predicates


class ImmersionLabel(BaseControlledSiteContentModel):
    """
    Represents a label that can be used to tag a dictionary entry for use as an FE immersion label.
    """

    class Meta:
        verbose_name = _("immersion label")
        verbose_name_plural = _("immersion labels")
        constraints = [
            models.UniqueConstraint(
                fields=["key", "site"],
                name="unique_label_keys_per_site",
            )
        ]
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.is_language_admin_or_super,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_language_admin_or_super,
        }
        indexes = [
            models.Index(fields=["site", "key"], name="immersion_label_key_idx"),
        ]

    key = models.SlugField(
        max_length=DEFAULT_TITLE_LENGTH,
        blank=False,
        validators=[validate_slug],
        db_index=True,
        unique=True,
    )

    dictionary_entry = models.ForeignKey(
        "DictionaryEntry",
        on_delete=models.CASCADE,
        related_name="immersion_labels",
    )

    def save(self, *args, **kwargs):
        # visibility is saved in the db rather than set as a property to make permissions simpler
        self.visibility = self.dictionary_entry.visibility
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Label: {self.key}:{self.dictionary_entry.title}"
