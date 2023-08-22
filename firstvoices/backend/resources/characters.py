from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.models.dictionary import DictionaryEntry, DictionaryEntryRelatedCharacter
from backend.resources.base import BaseResource, SiteContentResource


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


class CharacterRelatedDictionaryEntriesResource(BaseResource):
    character = fields.Field(
        column_name="character",
        attribute="character",
        widget=ForeignKeyWidget(Character, "id"),
    )
    dictionary_entry = fields.Field(
        column_name="dictionary_entry",
        attribute="dictionary_entry",
        widget=ForeignKeyWidget(DictionaryEntry, "id"),
    )

    class Meta:
        model = DictionaryEntryRelatedCharacter

    # todo: verify if we need to skip imports that don't exist
