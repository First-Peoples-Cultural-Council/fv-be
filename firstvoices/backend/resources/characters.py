from import_export import fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
from backend.models.dictionary import DictionaryEntry, DictionaryEntryRelatedCharacter
from backend.models.media import Audio, Video
from backend.resources.base import BaseResource, SiteContentResource


class CharacterResource(SiteContentResource):
    # add related media mapping
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
        widget=ManyToManyWidget(Video, "id"),
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
