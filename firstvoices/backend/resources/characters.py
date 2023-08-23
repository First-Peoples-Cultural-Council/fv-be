from import_export import fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from backend.models.characters import Character, CharacterVariant, IgnoredCharacter
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
