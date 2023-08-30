from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from backend.models.constants import MAX_NOTE_LENGTH
from backend.permissions import predicates

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

    Notes for data migration:
    acknowledgements from fvbook:acknowledgement
    notes from fv:cultural_note

    introduction from fvbook:introduction
    introduction_translation from fvbook:introduction_literal_translation

    title from dc:title
    title_translation from fvbook:title_literal_translation

    settings from a value in settings:settings
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

    def __str__(self):
        return self.title


class StoryPage(TranslatedTextMixin, RelatedMediaMixin, BaseControlledSiteContentModel):
    """
    Representing the pages within a story

    ordering enforces ordering via simple ascending sort

    translation from fvbookentry:dominant_language_text and fv:literal_translation
    text from dc:title
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
        # always match the site
        # these are saved in the db rather than set as properties to make permissions on queries simpler
        self.visibility = self.story.visibility
        self.site = self.story.site
        super().save(*args, **kwargs)

    def __str__(self):
        return f"'{self.story.title}' page {self.ordering}"
