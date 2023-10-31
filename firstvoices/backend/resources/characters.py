from import_export import fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from backend.models.characters import (
    Alphabet,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from backend.models.media import Audio, Video
from backend.resources.base import SiteContentResource


class CharacterResource(SiteContentResource):
    related_audio = fields.Field(
        column_name="related_audio",
        attribute="related_audio",
        m2m_add=True,
        widget=ManyToManyWidget(Audio, field="id"),
    )
    related_videos = fields.Field(
        column_name="related_videos",
        attribute="related_videos",
        m2m_add=True,
        widget=ManyToManyWidget(Video, field="id"),
    )

    class Meta:
        model = Character


class CharacterVariantResource(SiteContentResource):
    base_character = fields.Field(
        column_name="base_character",
        attribute="base_character",
        widget=ForeignKeyWidget(Character, "id"),
    )

    class Meta:
        model = CharacterVariant


class IgnoredCharacterResource(SiteContentResource):
    class Meta:
        model = IgnoredCharacter


class AlphabetConfusablesResource(SiteContentResource):
    "Convert rows to a JSON list and save to the site Alphabet."

    class Meta:
        model = Alphabet

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        if not dry_run:
            alphabet, _ = Alphabet.objects.get_or_create(site_id=dataset["site"][0])

            list_of_mappers = []
            for in_form, out_form in zip(dataset["in_form"], dataset["out_form"]):
                mapper = {"in": in_form, "out": out_form}
                list_of_mappers.append(mapper)

            alphabet.input_to_canonical_map = list_of_mappers
            alphabet.save()
        return super().before_import(dataset, using_transactions, dry_run, **kwargs)

    def skip_row(self, instance, original, row, import_validation_errors=None):
        "Never import individual rows."
        return True
