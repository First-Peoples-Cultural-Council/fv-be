import logging

import yaml
from django.core.exceptions import ValidationError
from django.db import models
from django.db.utils import IntegrityError
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from g2p.mappings import Mapping
from g2p.transducer import Transducer

from backend.permissions import predicates
from backend.utils.character_utils import CustomSorter, nfc

from .app import AppJson
from .base import BaseSiteContentModel
from .constants import MAX_CHARACTER_APPROXIMATE_FORM_LENGTH, MAX_CHARACTER_LENGTH
from .media import RelatedMediaMixin


class Character(RelatedMediaMixin, BaseSiteContentModel):
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
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,
            "change": predicates.is_language_admin_or_super,
            "delete": predicates.is_superadmin,
        }

        indexes = [
            models.Index(fields=["title", "site"], name="character_title_idx"),
        ]

    # from dc:title
    # Unique with site_id
    title = models.CharField(max_length=MAX_CHARACTER_LENGTH)

    # from fvcharacter:alphabet_order
    # Unique with site_id
    sort_order = models.IntegerField()

    # from fvcharacter:fuzzy_latin_match
    approximate_form = models.CharField(
        max_length=MAX_CHARACTER_APPROXIMATE_FORM_LENGTH, blank=True
    )

    # from fv:notes
    note = models.TextField(blank=True)

    # related_audio from fv:related_audio
    # related_images from fv:related_pictures
    # related_videos from fv:related_videos

    def __str__(self):
        return f"{self.title} - {self.site}"

    def save(self, *args, **kwargs):
        self.validate_character_limit()
        self.validate_title_uniqueness()
        super().save(*args, **kwargs)

    def validate_title_uniqueness(self):
        """
        Validates that the `title` field is unique across  the `Character`,`CharacterVariant`. and `IgnoredCharacter`
        models for a given `site_id`.
        """
        if CharacterVariant.objects.filter(
            site_id=self.site_id, title=self.title
        ).exists():
            raise IntegrityError(
                "The title %s is already used by a CharacterVariant with the same site_id."
                % self.title
            )
        elif IgnoredCharacter.objects.filter(
            site_id=self.site_id, title=self.title
        ).exists():
            raise IntegrityError(
                "The title %s is already used by an IgnoredCharacter with the same site_id."
                % self.title
            )

    def validate_character_limit(self):
        """
        Validates that the site has not already reached the max character limit.
        """
        limit = CustomSorter.max_alphabet_length
        if Character.objects.filter(site_id=self.site_id).count() >= limit:
            raise ValidationError("Over maximum character limit: %s chars" % limit)


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
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

        indexes = [
            models.Index(fields=["title", "site"], name="cv_site_title_idx"),
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
        self.validate_title_uniqueness()
        super().save(*args, **kwargs)

    def set_site_id(self):
        self.site = self.base_character.site

    def validate_title_uniqueness(self):
        """
        Validates that the `title` field is unique across  the `Character`,`CharacterVariant`. and `IgnoredCharacter`
        models for a given `site_id`.
        """
        if Character.objects.filter(site_id=self.site_id, title=self.title).exists():
            raise IntegrityError(
                "The title %s is already used by a Character with the same site_id."
                % self.title
            )
        elif IgnoredCharacter.objects.filter(
            site_id=self.site_id, title=self.title
        ).exists():
            raise IntegrityError(
                "The title %s is already used by an IgnoredCharacter with the same site_id."
                % self.title
            )


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
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

        indexes = [
            models.Index(fields=["title", "site"], name="ignoredcharacter_title_idx"),
        ]

    # from fv-alphabet:ignored_characters
    # Unique with site_id
    title = models.CharField(max_length=MAX_CHARACTER_LENGTH)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.validate_title_uniqueness()
        super().save(*args, **kwargs)

    def validate_title_uniqueness(self):
        """
        Validates that the `title` field is unique across  the `Character`,`CharacterVariant`. and `IgnoredCharacter`
        models for a given `site_id`.
        """
        if CharacterVariant.objects.filter(
            site_id=self.site_id, title=self.title
        ).exists():
            raise IntegrityError(
                "The title %s is already used by a CharacterVariant with the same site_id."
                % self.title
            )
        elif Character.objects.filter(site_id=self.site_id, title=self.title).exists():
            raise IntegrityError(
                "The title %s is already used by an Character with the same site_id."
                % self.title
            )


class Alphabet(BaseSiteContentModel):
    """
    Hosts text processors and sorters for a site's custom alphabet.
    """

    class Meta:
        verbose_name = _("alphabet")
        verbose_name_plural = _("alphabet")
        rules_permissions = {
            "view": predicates.is_superadmin,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    logger = logging.getLogger(__name__)

    # from all fv-character:confusables for a site
    # JSON representation of a g2p mapping from confusable characters to canonical characters
    input_to_canonical_map = models.JSONField(default=list)

    @cached_property
    def base_characters(self):
        """
        Characters for the site in sort order.
        """
        return Character.objects.filter(site=self.site).order_by("sort_order")

    @cached_property
    def variant_characters(self):
        """
        All variant characters for the site.
        """
        return CharacterVariant.objects.filter(site=self.site).select_related(
            "base_character"
        )

    @cached_property
    def ignorable_characters(self):
        """
        Ignorable characters for the site.
        """
        return IgnoredCharacter.objects.filter(site=self.site)

    @cached_property
    def default_g2p_config(self):
        """
        Returns default G2P configurations for required mappers, customized with site name and slug.
        """
        site_name = f"FV {self.site.title}"
        site_code = f"fv-{self.site.slug}"

        # Convert from default g2p config json to site-specific yaml
        default_config_str = yaml.dump(
            AppJson.objects.get(key="default_g2p_config").json, default_style='"'
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

            # need to query for self to grab unescaped json: see FW-4365, FW-4559
            readable_self = Alphabet.objects.only("input_to_canonical_map").get(
                id=self.id
            )
            return Transducer(
                Mapping(
                    **preprocess_settings,
                    rules=readable_self.input_to_canonical_map,
                )
            )
        else:
            self.logger.debug("Empty confusable map for site %s", self.site)
            return None

    def presort_transducer(self, base_characters=None, character_variants=None):
        """
        Returns a variant-to-base G2P transducer, built from Characters and CharacterVariants.
        """
        base_characters = (
            base_characters if base_characters is not None else self.base_characters
        )
        base_character_map = (
            [{"in": char.title, "out": char.title} for char in base_characters]
            if base_characters is not None
            else []
        )
        character_variants = (
            character_variants
            if character_variants is not None
            else self.variant_characters
        )
        variant_character_map = (
            [
                {"in": variant.title, "out": variant.base_character.title}
                for variant in character_variants
            ]
            if character_variants is not None
            else []
        )
        full_map = base_character_map + variant_character_map

        presort_settings = self.default_g2p_config["presort_config"]

        return Transducer(Mapping(**presort_settings, rules=full_map))

    def sorter(self, base_characters=None, ignorable_characters=None) -> CustomSorter:
        """
        Returns a sorter object which can be called to provide custom sort values based on the site alphabet.
        """
        base_characters = (
            base_characters if base_characters is not None else self.base_characters
        )
        ignorable_characters = (
            ignorable_characters
            if ignorable_characters is not None
            else self.ignorable_characters
        )
        return CustomSorter(
            order=[char.title for char in base_characters],
            ignorable=[char.title for char in ignorable_characters],
        )

    def splitter(
        self, base_characters=None, character_variants=None, ignorable_characters=None
    ) -> CustomSorter:
        """
        Returns a sorter object containing both base characters and character variants
        to properly split text into characters using the MTD splitter.
        Ignored characters are added to the order list to ensure they are not removed by the splitter.
        """
        base_characters = (
            base_characters if base_characters is not None else self.base_characters
        )
        character_variants = (
            character_variants
            if character_variants is not None
            else self.variant_characters
        )
        ignorable_characters = (
            ignorable_characters
            if ignorable_characters is not None
            else self.ignorable_characters
        )
        return CustomSorter(
            order=[char.title for char in base_characters]
            + [char.title for char in character_variants]
            + [char.title for char in ignorable_characters]
        )

    def __str__(self):
        return f"Alphabet and related functions for {self.site}"

    def clean_confusables(self, text: str) -> str:
        """
        Applies the mapper's confusable cleanup transducer to a string,
        converting all instances of confusables to instances of characters or
        variant characters.
        """
        if self.preprocess_transducer:
            new_text = self.preprocess_transducer(text).output_string
            return nfc(new_text)
        else:
            return text

    def get_custom_order(
        self,
        text: str,
        base_characters=None,
        character_variants=None,
        ignorable_characters=None,
    ) -> str:
        """
        Convert a string to a custom-order string which follows the site custom alphabet order.
        Sort is insensitive to character variants (such as uppercase), and ignores ignorable characters.
        """
        presort_transducer = self.presort_transducer(
            base_characters, character_variants
        )
        text = presort_transducer(text).output_string
        return self.sorter(base_characters, ignorable_characters).word_as_sort_string(
            text
        )

    def get_character_list(
        self,
        text: str,
        base_characters=None,
        character_variants=None,
        ignorable_characters=None,
    ) -> list[str]:
        """
        Returns a list of characters in the text, split using the MTD splitter.
        """
        return self.splitter(
            base_characters, character_variants, ignorable_characters
        ).word_as_chars(text)

    def get_base_form(
        self, text: str, base_characters=None, character_variants=None
    ) -> str:
        """
        Converts a string to a string with all variant characters replaced with their base characters.
        """
        presort_transducer = self.presort_transducer(
            base_characters, character_variants
        )
        return presort_transducer(text).output_string

    def get_numerical_sort_form(
        self,
        text,
        base_characters=None,
        character_variants=None,
        ignorable_characters=None,
    ):
        return self.sorter(base_characters, ignorable_characters).word_as_values(
            self.get_base_form(text, base_characters, character_variants)
        )

    def get_split_chars_base(
        self,
        entry,
        base_characters=None,
        character_variants=None,
        ignorable_characters=None,
    ) -> list[str]:
        ignored_characters = IgnoredCharacter.objects.filter(
            site=self.site
        ).values_list("title", flat=True)
        base_characters = (
            base_characters if base_characters is not None else self.base_characters
        )
        character_variants = (
            character_variants
            if character_variants is not None
            else self.variant_characters
        )
        ignorable_characters = (
            ignorable_characters
            if ignorable_characters is not None
            else self.ignorable_characters
        )
        if "⚑" in entry.custom_order:
            return []
        else:
            char_list = (
                []
                if self == []
                else self.get_character_list(
                    entry.title,
                    base_characters,
                    character_variants,
                    ignorable_characters,
                )
            )
            has_ignored_char = set(char_list).intersection(set(ignored_characters))
            if has_ignored_char:
                return []
            else:
                base_chars = [
                    self.get_base_form(
                        c,
                        base_characters,
                        character_variants,
                    )
                    for c in char_list
                ]
                return base_chars
