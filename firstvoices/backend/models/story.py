from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from backend.permissions import predicates

from .base import AudienceMixin, BaseControlledSiteContentModel, BaseModel
from .media import RelatedMediaMixin

TITLE_MAX_LENGTH = 500
NOTE_MAX_LENGTH = 1000


class Story(
    AudienceMixin,
    RelatedMediaMixin,
    BaseControlledSiteContentModel,
):
    """
    Representing a story associated with a site, including unique title, pages, introduction, and media links

    Notes for data migration:
    acknowledgements from fv:source and fvbook:author (which should be dereferenced)
    notes from fv:cultural_note

    introduction from fvbook:introduction
    introduction_translation from fvbook:introduction_literal_translation

    title from dc:title
    title_translation from fvbook:title_literal_translation

    settings from a value in settings:settings

    cover_image should be a duplicate of the first entry in fv:related_pictures for migration, can vary after that
    """

    class Meta:
        verbose_name_plural = "stories"
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    cover_image = models.ForeignKey(
        to="Image", on_delete=models.SET_NULL, related_name="story_cover_of", null=True
    )

    title = models.CharField(blank=False, null=False)
    title_translation = models.CharField(blank=True, null=False)

    introduction = models.CharField(blank=True, null=False)
    introduction_translation = models.CharField(blank=True, null=False)

    acknowledgements = ArrayField(
        models.TextField(max_length=NOTE_MAX_LENGTH), blank=True, default=list
    )
    notes = ArrayField(
        models.TextField(max_length=NOTE_MAX_LENGTH), blank=True, default=list
    )

    def __str__(self):
        return self.title


class StoryPage(BaseModel, RelatedMediaMixin):
    """
    Representing the pages within a story

    ordering enforces ordering via simple ascending sort

    translation from fvbook:lyrics_translation
    text from fvbook:lyrics
    """

    class Meta:
        unique_together = ("story", "ordering")
        ordering = ("ordering",)
        verbose_name = "story page"
        verbose_name_plural = "story pages"
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    story = models.ForeignKey("Story", related_name="pages", on_delete=models.CASCADE)

    ordering = models.SmallIntegerField(
        validators=[MinValueValidator(0)], null=False, default=0
    )

    text = models.TextField(max_length=NOTE_MAX_LENGTH, blank=False)
    translation = models.TextField(max_length=NOTE_MAX_LENGTH, blank=True)
