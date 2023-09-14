from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models import Lyric, Song
from backend.resources.base import (
    BaseResource,
    ControlledSiteContentResource,
    RelatedMediaResourceMixin,
)


class SongResource(ControlledSiteContentResource, RelatedMediaResourceMixin):
    class Meta:
        model = Song

    def before_save_instance(self, instance, using_transactions, dry_run):
        instance.acknowledgements = ",".join(instance.acknowledgements).split("|")
        instance.notes = ",".join(instance.notes).split("|")


class LyricResource(BaseResource):
    song = fields.Field(
        column_name="parent_id",
        attribute="song",
        widget=ForeignKeyWidget(Song, "id"),
    )
    array_sep = "|||"

    class Meta:
        model = Lyric

    def before_import_row(self, row, row_number=None, **kwargs):
        if not Song.objects.filter(id=row["parent_id"]).exists():
            row["parent_id"] = None

    def skip_row(self, instance, original, row, import_validation_errors=None):
        return not Song.objects.filter(id=row["parent_id"]).exists()

    def after_import_row(self, row, row_result, row_number=None, **kwargs):
        # If the book entry is a lyric and has notes, add them to the song
        if Song.objects.filter(id=row["parent_id"]).exists() and row["notes"] != "":
            song = Song.objects.get(id=row["parent_id"])

            for note in [
                string.strip() for string in row["notes"].split(sep=self.array_sep)
            ]:
                song.notes.append("From lyric: " + note)
            song.save()
