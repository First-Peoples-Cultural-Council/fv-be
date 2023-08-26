from import_export import fields

from backend.models import Song
from backend.models.constants import Visibility
from backend.resources.base import SiteContentResource
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
            "related_video",
            "hide_overlay",
        )

    def before_save_instance(self, instance, using_transactions, dry_run):
        instance.acknowledgements = ",".join(instance.acknowledgements).split("|")
        instance.notes = ",".join(instance.notes).split("|")
