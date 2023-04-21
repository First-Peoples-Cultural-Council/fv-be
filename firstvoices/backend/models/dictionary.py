from django.db import models
from django.utils.translation import gettext as _

from backend.utils.character_utils import clean_input

from .base import BaseControlledSiteContentModel, BaseModel, TruncatingCharField
from .category import Category
from .characters import Alphabet, Character
from .part_of_speech import PartOfSpeech

TITLE_MAX_LENGTH = 225


class BaseDictionaryContentModel(BaseModel):
    """
    Base model for Dictionary models which require DictionaryEntry as a foreign key and
    have site as a property but not as a field.
    """

    dictionary_entry = models.ForeignKey(
        "DictionaryEntry", on_delete=models.CASCADE, related_name="dictionary_%(class)s"
    )

    @property
    def site(self):
        """Returns the site that the DictionaryEntry model is associated with."""
        return self.dictionary_entry.site

    class Meta:
        abstract = True


class DictionaryNote(BaseDictionaryContentModel):
    """Model for notes associated to each dictionary entry."""

    # from fv:notes,fv:general_note, fv:cultural_note, fv:literal_translation, fv-word:notes, fv-phrase:notes
    text = models.TextField()

    def __str__(self):
        return self.text


class DictionaryAcknowledgement(BaseDictionaryContentModel):
    """Model for acknowledgments associated to each dictionary entry."""

    # from fv:acknowledgments, fv:source, fv:reference, fv-word:acknowledgement, fv-phrase:acknowledgement
    text = models.TextField()

    def __str__(self):
        return self.text


class DictionaryTranslation(BaseDictionaryContentModel):
    """Model for translations associated to each dictionary entry."""

    class TranslationLanguages(models.TextChoices):
        # Choices for Language
        ENGLISH = "EN", _("English")
        FRENCH = "FR", _("French")

    # Fields
    text = models.CharField(max_length=TITLE_MAX_LENGTH)
    language = models.CharField(
        max_length=2,
        choices=TranslationLanguages.choices,
        default=TranslationLanguages.ENGLISH,
    )
    # from fv-word:part_of_speech
    part_of_speech = models.ForeignKey(
        PartOfSpeech,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="translations",
    )

    def __str__(self):
        return _("Translation in %(language)s: %(translation)s.") % {
            "language": self.language,
            "translation": self.text,
        }


class AlternateSpelling(BaseDictionaryContentModel):
    """Model for alternate spellings associated to each dictionary entry."""

    # from fv:alternate_spelling, fv-word:alternate_spellings, fv-phrase:alternate_spellings
    text = models.CharField(max_length=TITLE_MAX_LENGTH)

    def __str__(self):
        return self.text


class Pronunciation(BaseDictionaryContentModel):
    """Model for pronunciations associated to each dictionary entry."""

    # from fv-word:pronunciation
    text = models.CharField(max_length=TITLE_MAX_LENGTH)

    def __str__(self):
        return self.text


class DictionaryEntry(BaseControlledSiteContentModel):
    """Model for dictionary entries
    TruncatingCharField for custom_order: For each unknown character, we get 2 characters in the custom order field
    (one character and one flag) used for sorting purposes. There is not much use of retaining sorting information
    after ~112 characters incase there are words which contain all 225 unknown characters. Thus, the field gets
    truncated at max length.
    """

    class TypeOfDictionaryEntry(models.TextChoices):
        # Choices for Type
        WORD = "WORD", _("Word")
        PHRASE = "PHRASE", _("Phrase")

    # Fields
    # from dc:title, relatively more max_length due to phrases
    # see fw-4196, max_length may be modified after doing some analysis on the length of current phrases
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
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
    custom_order = TruncatingCharField(max_length=TITLE_MAX_LENGTH, blank=True)
    # from fv-word:available_in_games, fvaudience:games
    exclude_from_games = models.BooleanField(default=False)
    # from fvaudience:children fv:available_in_childrens_archive
    # exclude_from_kids can be a shared mixin for dictionary_entries, songs, stories and media
    exclude_from_kids = models.BooleanField(default=False)
    # from nxtag:tags
    batch_id = models.CharField(max_length=255, blank=True)
    # from fv:related_assets, fv-word:related_phrases
    related_dictionary_entries = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        through="DictionaryEntryLink",
        related_name="incoming_related_dictionary_entries",
    )

    # from fvcharacter:related_words
    related_characters = models.ManyToManyField(
        Character,
        blank=True,
        through="DictionaryEntryRelatedCharacter",
        related_name="dictionary_entries",
    )

    class Meta:
        verbose_name = _("Dictionary Entry")
        verbose_name_plural = _("Dictionary Entries")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        alphabet, created = Alphabet.objects.get_or_create(site_id=self.site_id)

        self.clean_title(alphabet)
        self.set_custom_order(alphabet)
        super().save(*args, **kwargs)

    def clean_title(self, alphabet):
        # strip whitespace and normalize
        self.title = clean_input(self.title)
        # clean confusables
        self.title = alphabet.clean_confusables(self.title)

    def set_custom_order(self, alphabet):
        self.custom_order = alphabet.get_custom_order(self.title)


class DictionaryEntryLink(models.Model):
    from_dictionary_entry = models.ForeignKey(DictionaryEntry, on_delete=models.CASCADE)
    to_dictionary_entry = models.ForeignKey(
        DictionaryEntry,
        on_delete=models.CASCADE,
        related_name="incoming_related_entries",
    )


class DictionaryEntryRelatedCharacter(models.Model):
    """
    Represents a link between a dictionary entry and  a character.
    """

    class Meta:
        verbose_name = _("character related dictionary entry")
        verbose_name_plural = _("character related dictionary entries")

    character = models.ForeignKey(
        Character,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="dictionary_entry_links",
    )

    dictionary_entry = models.ForeignKey(
        DictionaryEntry,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="character_links",
    )

    def __str__(self):
        return f"{self.character} - {self.dictionary_entry}"

    def save(self, *args, **kwargs):
        self.set_site_id()
        super().save(*args, **kwargs)

    def set_site_id(self):
        self.site = self.character.site
