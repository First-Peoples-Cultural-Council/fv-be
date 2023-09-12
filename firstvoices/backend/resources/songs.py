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

    class Meta:
        model = Lyric

    def before_import_row(self, row, row_number=None, **kwargs):
        if not Song.objects.filter(id=row["parent_id"]).exists():
            row["parent_id"] = None

    def skip_row(self, instance, original, row, import_validation_errors=None):
        return not Song.objects.filter(id=row["parent_id"]).exists()
