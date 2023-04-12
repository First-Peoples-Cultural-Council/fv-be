import logging

import g2p
import yaml
from django.db import models
from django.utils.translation import gettext as _

from ..utils.character_utils import CustomSorter
from .app import AppJson
from .constants import MAX_CHARACTER_LENGTH
from .sites import BaseSiteContentModel


class Character(BaseSiteContentModel):
    """
    Represents an alphabet character in a site.
    """

    # from FVCharacter type

    class Meta:
        verbose_name = _("character")
        verbose_name_plural = _("characters")
        constraints = [
            models.UniqueConstraint(
                fields=["title", "site_id"], name="unique_character"
            ),
            models.UniqueConstraint(
                fields=["sort_order", "site_id"], name="unique_character_sort_order"
            ),
        ]

    # from dc:title
    # Unique with site_id
    title = models.CharField(max_length=MAX_CHARACTER_LENGTH)

    # from fvcharacter:alphabet_order
    # Unique with site_id
    sort_order = models.IntegerField()

    # from fvcharacter:fuzzy_latin_match
    approximate_form = models.CharField(max_length=MAX_CHARACTER_LENGTH, blank=True)

    # from fv:notes
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.site}"


class CharacterVariant(BaseSiteContentModel):
    """
    Represents a canonical variant of a character in a site.
    """

    class Meta:
        verbose_name = _("character variant")
        verbose_name_plural = _("character variants")
        constraints = [
            models.UniqueConstraint(
                fields=["title", "site_id"], name="unique_character_variant"
            )
        ]

    # from fvcharacter: upper_case_character
    # Unique with site_id
    title = models.CharField(max_length=MAX_CHARACTER_LENGTH)

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
        constraints = [
            models.UniqueConstraint(
                fields=["title", "site_id"], name="unique_ignored_character"
            )
        ]

    # from fv-alphabet:ignored_characters
    # Unique with site_id
    title = models.CharField(max_length=MAX_CHARACTER_LENGTH)

    def __str__(self):
        return self.title


class Alphabet(BaseSiteContentModel):
    """
    Hosts text processors and sorters for a site's custom alphabet.
    """

    class Meta:
        verbose_name = _("alphabet mapper")
        verbose_name_plural = _("alphabet mappers")

    logger = logging.getLogger(__name__)

    # from all fv-character:confusables for a site
    # JSON representation of a g2p mapping from confusable characters to canonical characters
    input_to_canonical_map = models.JSONField(blank=True, default=list)

    @property
    def base_characters(self):
        """
        Characters for the site in sort order.
        """
        return Character.objects.filter(site=self.site).order_by("sort_order")

    @property
    def variant_characters(self):
        """
        All variant characters for the site.
        """
        return CharacterVariant.objects.filter(site=self.site)

    @property
    def ignorable_characters(self):
        """
        Ignorable characters for the site.
        """
        return IgnoredCharacter.objects.filter(site=self.site)

    @property
    def default_g2p_config(self):
        """
        Returns default G2P configurations for required mappers, customized with site name and slug.
        """
        site_name = f"FV {self.site.title}"
        site_code = f"fv-{self.site.slug}"

        # Convert from default g2p config json to site-specific yaml
        default_config_str = yaml.dump(
            AppJson.objects.get(key="default_g2p_config").json
        )
        site_config_str = default_config_str.format(language=site_name, code=site_code)
        site_config = yaml.safe_load(site_config_str)

        return site_config

    @property
    def preprocess_transducer(self):
        """
        Returns an input-to-canonical G2P transducer from stored JSON map, using default config settings.
        Does not allow manual configuration yet.
        """
        if self.input_to_canonical_map:
            preprocess_settings = self.default_g2p_config["preprocess_config"]

            return g2p.Transducer(
                g2p.Mapping(**preprocess_settings, mapping=self.input_to_canonical_map)
            )
        else:
            self.logger.warning("No confusable map found for site %s", self.site)
            return None

    def clean_confusables(self, text: str) -> str:
        """
        Applies the mapper's confusable cleanup transducer to a string,
        converting all instances of confusables to instances of characters or
        variant characters.
        """
        if self.preprocess_transducer:
            return self.preprocess_transducer(text).output_string
        else:
            return text

    @property
    def presort_transducer(self):
        """
        Returns a variant-to-base G2P transducer, built from Characters and CharacterVariants.
        """
        base_character_map = [
            {"in": char.title, "out": char.title} for char in self.base_characters
        ]
        variant_character_map = [
            {"in": variant.title, "out": variant.base_character.title}
            for variant in self.variant_characters
        ]
        full_map = base_character_map + variant_character_map

        presort_settings = self.default_g2p_config["presort_config"]

        return g2p.Transducer(g2p.Mapping(**presort_settings, mapping=full_map))

    def __str__(self):
        return f"Confusable mapper for {self.site}"

    @property
    def sorter(self) -> CustomSorter:
        """
        Returns a sorter object which can be called to provide custom sort values based on the site alphabet.
        """

        return CustomSorter(
            order=[char.title for char in self.base_characters],
            ignorable=[char.title for char in self.ignorable_characters],
        )

    def get_custom_order(self, text: str) -> str:
        """
        Convert a string to a custom-order string which follows the site custom alphabet order.
        Sort is insensitive to character variants (such as uppercase), and ignores ignorable characters.
        """
        text = self.presort_transducer(text).output_string
        return self.sorter.word_as_sort_string(text)
