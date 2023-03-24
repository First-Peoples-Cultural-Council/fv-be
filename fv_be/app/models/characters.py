from django.db import models
from django.utils.translation import gettext as _

# FirstVoices
from .constants import MAX_CHARACTER_LENGTH
from .dictionary import DictionaryEntry
from .sites import BaseSiteContentModel


class Character(BaseSiteContentModel):
    """
    Represents an alphabet character in a site.
    """

    # from FVCharacter type

    class Meta:
        verbose_name = _("character")
        verbose_name_plural = _("characters")

    # from dc:title
    title = models.CharField(max_length=MAX_CHARACTER_LENGTH, unique=True)

    # from fvcharacter:alphabet_order
    sort_order = models.IntegerField(unique=True)

    # from fvcharacter:fuzzy_latin_match
    approximate_form = models.CharField(max_length=MAX_CHARACTER_LENGTH, blank=True)

    # from fv:notes
    notes = models.TextField(blank=True)

    # from fvcharacter:related_words
    related_dictionary_entries = models.ManyToManyField(
        DictionaryEntry,
        blank=True,
        null=True,
        related_name="characters",
    )

    def __str__(self):
        return self.title


class CharacterVariant(BaseSiteContentModel):
    """
    Represents a canonical variant of a character in a site.
    """

    class Meta:
        verbose_name = _("character variant")
        verbose_name_plural = _("character variants")

    # from fvcharacter: upper_case_character
    title = models.CharField(max_length=MAX_CHARACTER_LENGTH, unique=True)

    base_character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name="variants"
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.set_site_id()
        super().save(*args, **kwargs)

    def set_site_id(self):
        self.site = self.base_character.site


class IgnoredCharacter(BaseSiteContentModel):
    """
    Represents a character that is ignored during sort in a site.
    """

    class Meta:
        verbose_name = _("ignored character")
        verbose_name_plural = _("ignored characters")

    # from fv-alphabet:ignored_characters
    title = models.CharField(max_length=MAX_CHARACTER_LENGTH, unique=True)

    def __str__(self):
        return self.title


# TODO: AlphabetMapper model implementation once g2p work has been completed
# class AlphabetMapper(BaseSiteContentModel):
#     """
#     Represents a private table holding the g2p mappings and configuration for a site.
#     """
#
#     class Meta:
#         verbose_name = _("alphabet mapper")
#         verbose_name_plural = _("alphabet mappers")
#
#     # TODO: Once file storage is configured, enable these FileFields / change to proper paths
#     # alphabet_mapper is a placeholder for now.
#     # input_to_canonical = models.FileField(upload_to="alphabet_mapper")
#     # canonical_to_base = models.FileField(upload_to="alphabet_mapper")
#     # g2p_config = models.FileField(upload_to="alphabet_mapper")
#
#     def __str__(self):
#         return self.id
