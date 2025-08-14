from django.core.validators import MinValueValidator
from django.db import models
from django_better_admin_arrayfield.models.fields import ArrayField

from backend.models.constants import MAX_NOTE_LENGTH
from backend.permissions import predicates
from backend.utils.character_utils import clean_input

from .base import (
    AudienceMixin,
    BaseControlledSiteContentModel,
    TranslatedIntroMixin,
    TranslatedTextMixin,
    TranslatedTitleMixin,
)
from .media import RelatedMediaMixin


class Story(
    TranslatedTitleMixin,
    TranslatedIntroMixin,
    AudienceMixin,
    RelatedMediaMixin,
    BaseControlledSiteContentModel,
):
    """
    Representing a story associated with a site, including unique title, pages, introduction, and media links
    """

    class Meta:
        verbose_name_plural = "stories"
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.can_add_controlled_data,
            "change": predicates.can_edit_controlled_data,
            "delete": predicates.can_delete_controlled_data,
        }

    # from fvbook:author
    author = models.CharField(max_length=200, blank=True)

    acknowledgements = ArrayField(
        models.CharField(max_length=MAX_NOTE_LENGTH), blank=True, default=list
    )

    notes = ArrayField(
        models.CharField(max_length=MAX_NOTE_LENGTH), blank=True, default=list
    )

    # from settings:settings json value
    hide_overlay = models.BooleanField(null=False, default=False)

    def save(self, *args, **kwargs):
        # normalizing text input
        self.acknowledgements = [
            clean_input(x) for x in self.acknowledgements if x is not None
        ]
        self.notes = [clean_input(x) for x in self.notes if x is not None]

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class StoryPage(TranslatedTextMixin, RelatedMediaMixin, BaseControlledSiteContentModel):
    """
    Representing the pages within a story

    ordering enforces ordering via simple ascending sort
    """

    class Meta:
        unique_together = ("story", "ordering")
        ordering = ("ordering",)
        verbose_name = "story page"
        verbose_name_plural = "story pages"
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.can_add_controlled_data,
            "change": predicates.can_edit_controlled_data,
            "delete": predicates.can_delete_controlled_data,
        }

    story = models.ForeignKey("Story", related_name="pages", on_delete=models.CASCADE)

    ordering = models.SmallIntegerField(
        validators=[MinValueValidator(0)], null=False, default=0
    )

    # from fv:cultural_note
    notes = ArrayField(
        models.CharField(max_length=MAX_NOTE_LENGTH), blank=True, default=list
    )

    def save(self, *args, **kwargs):
        # normalizing text input
        self.notes = [clean_input(x) for x in self.notes]

        # always match the site
        # these are saved in the db rather than set as properties to make permissions on queries simpler
        self.visibility = self.story.visibility
        self.site = self.story.site
        super().save(*args, **kwargs)

    def __str__(self):
        return f"'{self.story.title}' page {self.ordering}"
