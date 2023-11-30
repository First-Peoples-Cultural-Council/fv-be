from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import BaseSiteContentModel
from backend.models.constants import DEFAULT_TITLE_LENGTH
from backend.permissions import predicates


class ImmersionLabel(BaseSiteContentModel):
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
            "view": predicates.has_visible_site,
            "add": predicates.is_language_admin_or_super,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_language_admin_or_super,
        }
        indexes = [
            models.Index(fields=["site", "key"], name="immersion_label_key_idx"),
        ]

    key = models.CharField(max_length=DEFAULT_TITLE_LENGTH)

    dictionary_entry = models.ForeignKey(
        "DictionaryEntry",
        null=True,
        on_delete=models.SET_NULL,
        related_name="immersion_labels",
    )
