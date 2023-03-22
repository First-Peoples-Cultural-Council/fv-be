from django.db import models
from django.utils.translation import gettext as _

# FirstVoices
from .sites import BaseSiteContentModel, BaseControlledSiteContentModel
from .category import Category
from .part_of_speech import PartOfSpeech


class Note(BaseSiteContentModel):
    """Model for notes associated to each dictionary entry."""

    # from fv:notes,fv:general_note, fv:cultural_note, fv:literal_translation, fv-word:notes, fv-phrase:notes
    text = models.TextField()
    dictionary_entry = models.ForeignKey(
        "DictionaryEntry", on_delete=models.CASCADE, related_name="notes"
    )

    def __str__(self):
        return self.text


class Acknowledgement(BaseSiteContentModel):
    """Model for acknowledgments associated to each dictionary entry."""

    # from fv:acknowledgments, fv:source, fv:reference, fv-word:acknowledgement, fv-phrase:acknowledgement
    text = models.TextField()
    # todo: Confirm if this should be moved to dictionaryEntry, M:M relation
    dictionary_entry = models.ForeignKey(
        "DictionaryEntry", on_delete=models.CASCADE, related_name="acknowledgements"
    )

    def __str__(self):
        return self.text


class Translation(BaseSiteContentModel):
    """Model for translations associated to each dictionary entry."""

    class TranslationLanguages(models.TextChoices):
        # Choices for Language
        ENGLISH = "EN", _("English")
        FRENCH = "FR", _("French")

    # Fields
    text = models.CharField(max_length=200)
    language = models.CharField(
        max_length=2,
        choices=TranslationLanguages.choices,
        default=TranslationLanguages.ENGLISH,
    )
    # from fv-word:part_of_speech
    part_of_speech = models.ForeignKey(
        PartOfSpeech, on_delete=models.SET_NULL, blank=True, null=True, related_name="translations"
    )
    dictionary_entry = models.ForeignKey(
        "DictionaryEntry", on_delete=models.CASCADE, related_name="translations"
    )

    def __str__(self):
        return _("Translation in %(language)s: %(translation)s.") % {
            "language": self.language,
            "translation": self.translation,
        }


class AlternateSpelling(BaseSiteContentModel):
    """Model for alternate spellings associated to each dictionary entry."""

    # from fv:alternate_spelling, fv-word:alternate_spellings, fv-phrase:alternate_spellings
    text = models.CharField(max_length=200)
    dictionary_entry = models.ForeignKey(
        "DictionaryEntry", on_delete=models.CASCADE, related_name="alternate_spellings"
    )

    def __str__(self):
        return self.text


class Pronunciation(BaseSiteContentModel):
    """Model for pronunciations associated to each dictionary entry."""

    # from fv-word:pronunciation
    text = models.CharField(max_length=200)
    dictionary_entry = models.ForeignKey(
        "DictionaryEntry", on_delete=models.CASCADE, related_name="pronunciations"
    )

    def __str__(self):
        return self.text


class DictionaryEntry(BaseControlledSiteContentModel):
    """Model for dictionary entries"""

    class TypeOfDictionaryEntry(models.TextChoices):
        # Choices for Type
        WORD = "WORD", _("Word")
        PHRASE = "PHRASE", _("Phrase")

    # Fields
    # from dc:title, relatively more max_length due to phrases
    # todo: max_length may be modified after doing some analysis on the length of current phrases
    title = models.CharField(max_length=800)
    type = models.CharField(
        max_length=6,
        choices=TypeOfDictionaryEntry.choices,
        default=TypeOfDictionaryEntry.WORD,
    )
    # from fv-word:categories, fv-phrase:phrase_books
    categories = models.ForeignKey(
        Category,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="dictionary_entries",
    )
    # from fv:custom_order
    custom_order = models.CharField(max_length=800, blank=True)
    # from fv-word:available_in_games, fvaudience:games
    exclude_from_games = models.BooleanField(default=False)
    # from fvaudience:children fv:available_in_childrens_archive
    # exclude_from_kids can be a shared mixin for dictionary_entries, songs, stories and media
    exclude_from_kids = models.BooleanField(default=False)
    batch_id = models.CharField(max_length=255, blank=True)
    # from fv:related_assets, fv-word:related_phrases
    related_dictionary_entries = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        through="DictionaryEntryLink",
        related_name="incoming_related_dictionary_entries",
    )

    class Meta:
        verbose_name = _("DictionaryEntry")
        verbose_name_plural = _("DictionaryEntries")

    def __str__(self):
        return self.title


class DictionaryEntryLink(models.Model):
    from_dictionary_entry = models.ForeignKey(DictionaryEntry, on_delete=models.CASCADE)
    to_dictionary_entry = models.ForeignKey(
        DictionaryEntry,
        on_delete=models.CASCADE,
        related_name="incoming_related_entries",
    )
