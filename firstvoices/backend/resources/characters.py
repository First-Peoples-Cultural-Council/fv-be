import logging

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
        column_name="related_video",
        attribute="related_videos",
        m2m_add=True,
        widget=ManyToManyWidget(Video, "id"),
    )

    class Meta:
        model = Character

    def before_import_row(self, row, row_number=None, **kwargs):
        logger = logging.getLogger(__name__)

        if row["related_audio"] != "":
            audio_obj = Audio.objects.filter(id=row["related_audio"])
            if len(audio_obj) == 0:
                # Audio obj not found
                logger.warning(f"Missing audio obj for character {row['id']}.")
                row["related_audio"] = ""

        if row["related_videos"] != "":
            video_obj = Video.objects.filter(id=row["related_video"])
            if len(video_obj) == 0:
                # Video obj not found
                logger.warning(f"Missing video obj for character {row['id']}.")
                row["related_videos"] = ""


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
