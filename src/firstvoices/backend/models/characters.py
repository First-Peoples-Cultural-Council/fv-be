import json

import g2p
import yaml
from django.db import models
from django.utils.translation import gettext as _

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


class AlphabetMapper(BaseSiteContentModel):
    """
    Represents a private table holding the confusable g2p mapping and configuration for a site.
    """

    class Meta:
        verbose_name = _("alphabet mapper")
        verbose_name_plural = _("alphabet mappers")

    # from fv-alphabet:confusable_characters
    # JSON representation of a g2p mapping from confusable characters to canonical characters
    input_to_canonical_map = models.JSONField()

    @property
    def g2p_config(self):
        site_name = f"FV {self.site.title}"
        site_code = f"fv-{self.site.slug}"

        # Convert from default g2p config json to site-specific yaml
        default_config_str = yaml.dump(
            AppJson.objects.get(key="default_g2p_config").json
        )
        # print("default_config_str:", default_config_str)
        site_config_str = default_config_str.format(language=site_name, code=site_code)
        # print(site_config_str)
        site_config = yaml.safe_load(site_config_str)

        g2p_config = {
            "site_name": site_name,
            "site_code": site_code,
            "site_config": site_config,
        }

        return g2p_config

    @property
    def preprocess_transducer(self):
        site_config = self.g2p_config["site_config"]
        site_code = self.g2p_config["site_code"]
        # identify mapper for preprocess transducer
        input_name = site_code + "-input"
        canonical_name = site_code

        for mapping in site_config["mappings"]:
            if (
                mapping["in_lang"] == input_name
                and mapping["out_lang"] == canonical_name
            ):
                preprocess_settings = mapping
            else:
                # TODO: raise error if no mapping found
                pass

        preprocessor = g2p.Transducer(
            g2p.Mapping(**preprocess_settings, mapping=self.input_to_canonical_map)
        )

        return preprocessor

    @property
    def presort_transducer(self):
        base_characters = Character.objects.filter(site=self.site)
        variant_characters = CharacterVariant.objects.filter(site=self.site)

        site_config = self.g2p_config["site_config"]
        site_code = self.g2p_config["site_code"]

        base_character_info = [
            {"title": char.title, "order": char.sort_order} for char in base_characters
        ]
        variant_character_map = [
            {variant.title: variant.base_character.title}
            for variant in variant_characters
        ]

        variant_character_map.update(
            {char["title"]: char["title"] for char in base_character_info}
        )

        presorter_map = json.dumps(
            [
                {"in": variant, "out": base}
                for variant, base in variant_character_map.items()
            ],
            ensure_ascii=False,
        )

        # identify mapper for presort transducer
        canonical_name = site_code
        output_name = site_code + "-base"

        for mapping in site_config["mappings"]:
            if (
                mapping["in_lang"] == canonical_name
                and mapping["out_lang"] == output_name
            ):
                presort_settings = mapping
            else:
                # TODO: raise error if no mapping found
                pass

        presorter = g2p.Transducer(
            g2p.Mapping(**presort_settings, mapping=json.loads(presorter_map))
        )

        return presorter

    def __str__(self):
        return f"Confusable mapper for {self.site}"
