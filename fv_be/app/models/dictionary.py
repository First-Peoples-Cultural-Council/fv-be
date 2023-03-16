from django.db import models
from django.utils.translation import gettext as _

# FirstVoices
from .base import BaseModel
from .category import Category
from .part_of_speech import PartOfSpeech


class Note(BaseModel):
    """Model for notes associated to each dictionary entry."""

    # from fv:notes,fv:general_note, fv:cultural_note, fv:literal_translation, fv-word:notes, fv-phrase:notes
    text = models.TextField()

    def __str__(self):
        return self.text


class Acknowledgment(BaseModel):
    """Model for acknowledgments associated to each dictionary entry."""

    # from fv:acknowledgments, fv:source, fv:reference, fv-word:acknowledgement, fv-phrase:acknowledgement
    text = models.TextField()

    def __str__(self):
        return self.text


class Translation(BaseModel):
    """Model for translations associated to each dictionary entry."""

    # Choices for Language
    ENGLISH_ENUM_KEY = "EN"
    FRENCH_ENUM_KEY = "FR"
    LANGUAGE_CHOICES = [
        (ENGLISH_ENUM_KEY, _("English")),
        (FRENCH_ENUM_KEY, _("French")),
    ]

    # Fields
    translation = models.CharField(max_length=200)
    language = models.CharField(
        max_length=2, choices=LANGUAGE_CHOICES, default=ENGLISH_ENUM_KEY
    )
    # from fv-word:part_of_speech
    part_of_speech = models.ManyToManyField(PartOfSpeech)
    # todo: more representative name for the following attribute ?
    parent = models.ForeignKey("DictionaryEntry", on_delete=models.CASCADE)

    def __str__(self):
        return _("Translation in %(language)s: %(translation)s.") % {
            "language": self.language,
            "translation": self.translation,
        }


class AlternateSpelling(BaseModel):
    """Model for alternate spellings associated to each dictionary entry."""

    # todo: more representative name for the following attribute ?
    # from fv:alternate_spelling, fv-word:alternate_spellings, fv-phrase:alternate_spellings
    text = models.CharField(max_length=200)
    # todo: more representative name for the following attribute ?
    parent = models.ForeignKey("DictionaryEntry", on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class Pronunciation(BaseModel):
    """Model for pronunciations associated to each dictionary entry."""

    # todo: more representative name for the following attribute ?
    # from fv-word:pronunciation
    text = models.CharField(max_length=200)
    # todo: more representative name for the following attribute ?
    parent = models.ForeignKey("DictionaryEntry", on_delete=models.CASCADE)

    def __str__(self):
        return self.text


class DictionaryEntry(BaseModel):
    """Model for dictionary entries"""

    # Choices for Type
    WORD_ENUM_KEY = "WORD"
    PHRASE_ENUM_KEY = "PHRASE"
    TYPE_OF_ENTRY_CHOICES = [(WORD_ENUM_KEY, _("Word")), (PHRASE_ENUM_KEY, _("Phrase"))]

    # Fields
    # from dc:title
    title = models.CharField(max_length=200)
    type = models.CharField(
        max_length=6, choices=TYPE_OF_ENTRY_CHOICES, default=WORD_ENUM_KEY
    )
    # todo: Link to site model when available
    # may be inherited from an abstract base class or mixin later
    # site = models.ForeignKey(
    #     'Site',
    #     on_delete=models.CASCADE
    # )
    notes = models.ForeignKey("Note", on_delete=models.SET_NULL, null=True)
    acknowledgments = models.ForeignKey(
        "Acknowledgment", on_delete=models.PROTECT, null=True
    )
    # from fv-word:categories, fv-phrase:phrase_books
    categories = models.ManyToManyField(Category)
    # from fv:custom_order
    custom_order = models.CharField(max_length=200, blank=True)
    # from fv-word:available_in_games, fvaudience:games
    exclude_from_games = models.BooleanField(default=False)
    # from fvaudience:children fv:available_in_childrens_archive
    # exclude_from_kids can be a shared mixin for dictionary_entries, songs, stories and media
    exclude_from_kids = models.BooleanField(default=False)
    batch_id = models.CharField(max_length=255, blank=True)
    # from fv:related_assets, fv-word:related_phrases
    related_dictionary_entries = models.ManyToManyField("self", blank=True)

    class Meta:
        verbose_name_plural = "DictionaryEntries"

    def __str__(self):
        return self.title
