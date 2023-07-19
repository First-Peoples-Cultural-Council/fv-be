import rules
from django.db import models
from django.utils.translation import gettext as _

from backend.permissions import predicates
from backend.utils.character_utils import clean_input

from .base import (
    AudienceMixin,
    BaseControlledSiteContentModel,
    BaseModel,
    BaseSiteContentModel,
    TruncatingCharField,
)
from .category import Category
from .characters import Alphabet, Character
from .media import RelatedMediaMixin
from .part_of_speech import PartOfSpeech

TITLE_MAX_LENGTH = 225


class BaseDictionaryContentModel(BaseModel):
    """
    Base model for Dictionary models which require DictionaryEntry as a foreign key and
    have site as a property but not as a field.
    """

    dictionary_entry = models.ForeignKey(
        "DictionaryEntry", on_delete=models.CASCADE, related_name="%(class)s_set"
    )

    @property
    def site(self):
        """Returns the site that the DictionaryEntry model is associated with."""
        return self.dictionary_entry.site

    class Meta:
        abstract = True


class Note(BaseDictionaryContentModel):
    """Model for notes associated to each dictionary entry."""

    class Meta:
        rules_permissions = {
            "view": rules.always_allow,  # see fw-4368
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # from fv:notes,fv:general_note, fv:cultural_note, fv:literal_translation, fv-word:notes, fv-phrase:notes
    text = models.TextField()

    def save(self, *args, **kwargs):
        self.text = clean_input(self.text)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.text


class Acknowledgement(BaseDictionaryContentModel):
    """Model for acknowledgments associated to each dictionary entry."""

    class Meta:
        rules_permissions = {
            "view": rules.always_allow,  # see fw-4368
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # from fv:acknowledgments, fv:source, fv:reference, fv-word:acknowledgement, fv-phrase:acknowledgement
    text = models.TextField()

    def save(self, *args, **kwargs):
        self.text = clean_input(self.text)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.text


class Translation(BaseDictionaryContentModel):
    """Model for translations associated to each dictionary entry."""

    class Meta:
        rules_permissions = {
            "view": rules.always_allow,  # see fw-4368
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # Fields
    text = models.CharField(max_length=TITLE_MAX_LENGTH)
    # from fv-word:part_of_speech
    part_of_speech = models.ForeignKey(
        PartOfSpeech,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="translations",
    )

    def save(self, *args, **kwargs):
        self.text = clean_input(self.text)
        super().save(*args, **kwargs)

    def __str__(self):
        return _("Translation: %(translation)s.") % {
            "translation": self.text,
        }


class AlternateSpelling(BaseDictionaryContentModel):
    """Model for alternate spellings associated to each dictionary entry."""

    class Meta:
        rules_permissions = {
            "view": rules.always_allow,  # see fw-4368
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # from fv:alternate_spelling, fv-word:alternate_spellings, fv-phrase:alternate_spellings
    text = models.CharField(max_length=TITLE_MAX_LENGTH)

    def __str__(self):
        return self.text


class Pronunciation(BaseDictionaryContentModel):
    """Model for pronunciations associated to each dictionary entry."""

    class Meta:
        rules_permissions = {
            "view": rules.always_allow,  # see fw-4368
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # from fv-word:pronunciation
    text = models.CharField(max_length=TITLE_MAX_LENGTH)

    def __str__(self):
        return self.text


class TypeOfDictionaryEntry(models.TextChoices):
    # Choices for Type
    WORD = "WORD", _("Word")
    PHRASE = "PHRASE", _("Phrase")


class DictionaryEntry(AudienceMixin, RelatedMediaMixin, BaseControlledSiteContentModel):
    """
    Model for dictionary entries
    """

    # from dc:title, relatively more max_length due to phrases
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    type = models.CharField(
        max_length=6,
        choices=TypeOfDictionaryEntry.choices,
        default=TypeOfDictionaryEntry.WORD,
    )
    # from fv-word:categories, fv-phrase:phrase_books
    categories = models.ManyToManyField(
        Category,
        blank=True,
        through="DictionaryEntryCategory",
        related_name="dictionary_entries",
    )
    #  from fv:custom_order
    #  For each unknown character, we get 2 characters in the custom order field
    #  (one character and one flag) used for sorting purposes. There is not much use of retaining sorting information
    #  after ~112 characters incase there are words which contain all 225 unknown characters. Thus, the field gets
    #  truncated at max length.
    custom_order = TruncatingCharField(max_length=TITLE_MAX_LENGTH, blank=True)

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
        related_name="related_dictionary_entries",
    )

    # Word of the day flag, if true, will not be included when looking for word-of-the-day
    exclude_from_wotd = models.BooleanField(default=False, blank=False)

    # exclude_from_games from fv-word:available_in_games, fvaudience:games
    # exclude_from_kids from fvaudience:children fv:available_in_childrens_archive
    # related_audio from fv:related_audio
    # related_images from fv:related_pictures
    # related_videos from fv:related_videos

    class Meta:
        verbose_name = _("Dictionary Entry")
        verbose_name_plural = _("Dictionary Entries")
        ordering = ["title"]
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        alphabet, _ = Alphabet.objects.get_or_create(site_id=self.site_id)

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


class DictionaryEntryLink(BaseModel):
    class Meta:
        verbose_name = _("related dictionary entry")
        verbose_name_plural = _("related dictionary entries")
        rules_permissions = {
            "view": rules.always_allow,  # see fw-4368
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    from_dictionary_entry = models.ForeignKey(
        DictionaryEntry,
        on_delete=models.CASCADE,
        related_name="dictionaryentrylink_set",
    )
    to_dictionary_entry = models.ForeignKey(
        DictionaryEntry,
        on_delete=models.CASCADE,
        related_name="incoming_dictionaryentrylink_set",
    )

    @property
    def site(self):
        return self.from_dictionary_entry.site

    def __str__(self):
        return f"{self.from_dictionary_entry} -> {self.to_dictionary_entry}"


class DictionaryEntryRelatedCharacter(BaseDictionaryContentModel):
    """
    Represents a many-to-many link between a dictionary entry and a character.
    """

    class Meta:
        verbose_name = _("character - dictionary entry relation")
        verbose_name_plural = _("character - dictionary entry relations")
        rules_permissions = {
            "view": rules.always_allow,  # see fw-4368
            "add": predicates.is_language_admin_or_super,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_superadmin,
        }

    character = models.ForeignKey(
        Character,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    dictionary_entry = models.ForeignKey(
        DictionaryEntry, blank=True, null=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.character} - {self.dictionary_entry}"


class DictionaryEntryCategory(BaseDictionaryContentModel):
    class Meta:
        verbose_name = _("category - dictionary entry relation")
        verbose_name_plural = _("category - dictionary entry relations")
        rules_permissions = {
            "view": rules.always_allow,  # see fw-4368
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    dictionary_entry = models.ForeignKey(
        DictionaryEntry,
        on_delete=models.CASCADE,
        related_name="dictionaryentrycategory_set",
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="dictionaryentrycategory_set"
    )

    def __str__(self):
        return f"{self.category} - {self.dictionary_entry}"


class WordOfTheDay(BaseSiteContentModel):
    """
    Table for word-of-the-day containing word and its respective date it was chosen to be wotd.
    """

    date = models.DateField(db_index=True)
    dictionary_entry = models.ForeignKey(
        "DictionaryEntry", on_delete=models.CASCADE, related_name="wotd_set"
    )

    class Meta:
        verbose_name = _("Word of the day")
        verbose_name_plural = _("Words of the day")
        unique_together = ("site", "date")
        ordering = ["-date"]
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    def __str__(self):
        return f"{self.dictionary_entry} - {self.date}"
