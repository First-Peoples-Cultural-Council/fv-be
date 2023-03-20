from django.db import models
from django.utils.translation import gettext as _

# FirstVoices
from .sites import BaseSiteContentModel


class Character(BaseSiteContentModel):
    """
    Represents a character in a site.
    """

    # from FVCharacter type

    class Meta:
        verbose_name = _("character")
        verbose_name_plural = _("characters")

    # from dc:title
    title = models.CharField(max_length=15)

    # from fvcharacter:alphabet_order
    sort_order = models.IntegerField()

    # from fv:custom_order
    sort_character = models.CharField(max_length=1, blank=True)

    # from fvcharacter:fuzzy_latin_match
    approximate_form = models.CharField(max_length=15, blank=True)

    # from fv:notes
    notes = models.TextField(blank=True)

    # from fvcharacter:related_words
    # TODO: add this as a foreign key to the dictionary entry model once it's created
    # related_dictionary_entries = models.ForeignKey(
    #     DictionaryEntry, on_delete=models.SET_NULL, blank=True, null=True, related_name="characters")

    def __str__(self):
        return self.title


class CharacterVariant(BaseSiteContentModel):
    """
    Represents a canonical variant of a character in a site.
    """

    class Meta:
        verbose_name = _("character variant")
        verbose_name_plural = _("character variants")

    title = models.CharField(max_length=15)

    base_key = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name="variants"
    )

    def __str__(self):
        return self.title


class IgnoredCharacter(BaseSiteContentModel):
    """
    Represents a character that is ignored during sort in a site.
    """

    class Meta:
        verbose_name = _("ignored character")
        verbose_name_plural = _("ignored characters")

    title = models.CharField(max_length=15)

    def __str__(self):
        return self.title


class AlphabetMapper(BaseSiteContentModel):
    """
    Represents a private table holding the g2p mappings and configuration for a site.
    """

    class Meta:
        verbose_name = _("alphabet mapper")
        verbose_name_plural = _("alphabet mappers")

    # TODO: Once file storage is configured, enable these FileFields / change to proper paths
    # alphabet_mapper is a placeholder for now.
    # input_to_canonical = models.FileField(upload_to="alphabet_mapper")
    # canonical_to_base = models.FileField(upload_to="alphabet_mapper")
    # g2p_config = models.FileField(upload_to="alphabet_mapper")

    def __str__(self):
        return self.id
