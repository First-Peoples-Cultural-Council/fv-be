from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from backend.models.constants import (
    DEFAULT_TITLE_LENGTH,
    MAX_NOTE_LENGTH,
    MAX_PAGE_LENGTH,
)
from backend.permissions import predicates
from backend.utils.character_utils import clean_input

from .base import AudienceMixin, BaseControlledSiteContentModel, BaseModel
from .media import RelatedMediaMixin


class Song(
    AudienceMixin,
    RelatedMediaMixin,
    BaseControlledSiteContentModel,
):
    """
    Representing a song associated with a site, including unique title, lyrics, introduction, and media links

    Notes for data migration:
    acknowledgements from fv:source and fvbook:author (which should be de-referenced)
    notes from fv:cultural_note

    introduction from fvbook:introduction
    introduction_translation from fvbook:introduction_literal_translation

    title from dc:title
    title_translation from fvbook:title_literal_translation

    settings from a value in settings:settings
    """

    class Meta:
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.can_add_controlled_data,
            "change": predicates.can_edit_controlled_data,
            "delete": predicates.can_delete_controlled_data,
        }

    title = models.CharField(max_length=DEFAULT_TITLE_LENGTH, blank=False, null=False)
    title_translation = models.CharField(
        max_length=DEFAULT_TITLE_LENGTH, blank=True, null=False
    )

    introduction = models.TextField(max_length=MAX_PAGE_LENGTH, blank=True, null=False)
    introduction_translation = models.TextField(
        max_length=MAX_PAGE_LENGTH, blank=True, null=False
    )

    acknowledgements = ArrayField(
        models.CharField(max_length=MAX_NOTE_LENGTH), blank=True, default=list
    )
    notes = ArrayField(
        models.CharField(max_length=MAX_NOTE_LENGTH), blank=True, default=list
    )

    hide_overlay = models.BooleanField(null=False, default=False)

    def save(self, *args, **kwargs):
        # normalizing text input
        self.title = clean_input(self.title)
        self.title_translation = clean_input(self.title_translation)
        self.introduction = clean_input(self.introduction)
        self.introduction_translation = clean_input(self.introduction_translation)
        self.acknowledgements = list(
            map(lambda x: clean_input(x), self.acknowledgements)
        )
        self.notes = list(map(lambda x: clean_input(x), self.notes))

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Lyric(BaseModel):
    """
    Representing the lyrics within a song

    ordering enforces ordering via simple ascending sort

    lyrics_translation from fvbook:lyrics_translation
    lyrics from fvbook:lyrics
    """

    class Meta:
        unique_together = ("song", "ordering")
        ordering = ("ordering",)
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    song = models.ForeignKey("Song", related_name="lyrics", on_delete=models.CASCADE)

    ordering = models.SmallIntegerField(
        validators=[MinValueValidator(0)], null=False, default=0
    )

    text = models.TextField(max_length=MAX_PAGE_LENGTH, blank=False)
    translation = models.TextField(max_length=MAX_PAGE_LENGTH, blank=True)

    def save(self, *args, **kwargs):
        # normalizing text input
        self.text = clean_input(self.text)
        self.translation = clean_input(self.translation)

        super().save(*args, **kwargs)
