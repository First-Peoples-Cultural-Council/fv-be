import rules
from backend import predicates
from backend.models.base import BaseModel
from backend.models.constants import CATEGORY_POS_MAX_TITLE_LENGTH
from backend.models.managers import PermissionsManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _


class ParentManager(PermissionsManager):
    """Manager to convert foreign key relationship to natural keys for fixtures to load correctly."""

    def get_by_natural_key(self, title):
        return self.get(title=title)


class PartOfSpeech(BaseModel):
    """Model for Parts Of Speech."""

    objects = ParentManager()

    # Fields
    title = models.CharField(max_length=CATEGORY_POS_MAX_TITLE_LENGTH, unique=True)
    # i.e. A PartOfSpeech may have a parent, but the parent PartOfSpeech cannot have a parent itself.
    # (i.e. no grandparents). This is enforced in the clean method.
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )

    class Meta:
        verbose_name = _("Part Of Speech")
        verbose_name_plural = _("Parts Of Speech")
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    def __str__(self):
        return self.title

    def natural_key(self):
        return (self.title,)

    def clean(self):
        self.is_cleaned = True
        # Enforce only one max level of nesting
        parent_part_of_speech = self.parent
        if parent_part_of_speech and parent_part_of_speech.parent:
            raise ValidationError(
                _(
                    "A PartOfSpeech may have a parent, but the parent PartOfSpeech cannot have a "
                    "parent itself. (i.e. no grandparents)"
                )
            )
        super().clean()

    def save(self, *args, **kwargs):
        # Inputs coming from other sources than forms may not have this attribute present
        # to validate those inputs as well, this attributed is added explicitly
        if not hasattr(self, "is_cleaned"):
            self.is_cleaned = False
        if not self.is_cleaned:
            self.full_clean()
        super().save(*args, **kwargs)
