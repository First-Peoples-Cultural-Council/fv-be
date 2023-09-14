from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models import Lyric, Song
from backend.resources.base import (
    BaseResource,
    ControlledSiteContentResource,
    RelatedMediaResourceMixin,
)
from backend.resources.utils.import_export_widgets import ArrayOfStringsWidget


class SongResource(ControlledSiteContentResource, RelatedMediaResourceMixin):
    acknowledgements = fields.Field(
        column_name="acknowledgements",
        attribute="acknowledgements",
        widget=ArrayOfStringsWidget(sep="|"),
    )
    notes = fields.Field(
        column_name="notes",
        attribute="notes",
        widget=ArrayOfStringsWidget(sep="|"),
    )

    class Meta:
        model = Song


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
