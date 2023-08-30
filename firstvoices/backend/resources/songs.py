from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models import Lyric, Song
from backend.models.constants import Visibility
from backend.resources.base import BaseResource, SiteContentResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class SongResource(SiteContentResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    class Meta:
        model = Song
        fields = (
            "id",
            "title",
            "title_translation",
            "visibility",
            "site",
            "introduction",
            "introduction_translation",
            "acknowledgements",
            "notes",
            "exclude_from_games",
            "exclude_from_kids",
            "related_audio",
            "related_images",
            "related_videos",
            "hide_overlay",
        )

    def before_save_instance(self, instance, using_transactions, dry_run):
        instance.acknowledgements = ",".join(instance.acknowledgements).split("|")
        instance.notes = ",".join(instance.notes).split("|")


class LyricResource(BaseResource):
    song = fields.Field(
        column_name="parent_id",
        attribute="song",
        widget=ForeignKeyWidget(Song, "id"),
    )

    class Meta:
        model = Lyric
        fields = ("id", "text", "translation", "song", "ordering")

    def before_import_row(self, row, row_number=None, **kwargs):
        if not Song.objects.filter(id=row["parent_id"]).exists():
            row["parent_id"] = None

    def skip_row(self, instance, original, row, import_validation_errors=None):
        return not Song.objects.filter(id=row["parent_id"]).exists()
