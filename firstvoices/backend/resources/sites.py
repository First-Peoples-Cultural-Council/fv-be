from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models.constants import Visibility
from backend.models.sites import Language, Site
from backend.resources.base import BaseResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class SiteResource(BaseResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    language = fields.Field(
        column_name="language",
        attribute="language",
        widget=ForeignKeyWidget(Language, "title"),
    )

    class Meta:
        model = Site


class SiteMigrationResource(SiteResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        """Before importing sites that already exist, delete and import fresh."""
        if not dry_run:
            Site.objects.filter(id__in=dataset["id"]).delete()
