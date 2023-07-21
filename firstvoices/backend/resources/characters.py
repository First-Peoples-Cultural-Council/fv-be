from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.resources.base import SiteContentResource


class CharacterResource(SiteContentResource):
    # add related media mapping

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
