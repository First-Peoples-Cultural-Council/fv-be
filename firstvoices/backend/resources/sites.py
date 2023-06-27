from import_export import fields, resources

from backend.models.constants import Visibility
from backend.models.sites import Site
from backend.resources.utils.import_export_widgets import (
    ChoicesWidget,
    UserForeignKeyWidget,
)


class BaseResource(resources.ModelResource):
    created_by = fields.Field(
        column_name="created_by",
        attribute="created_by",
        widget=UserForeignKeyWidget(create=False),
    )
    last_modified_by = fields.Field(
        column_name="last_modified_by",
        attribute="last_modified_by",
        widget=UserForeignKeyWidget(create=False),
    )

    class Meta:
        abstract = True


class SiteResource(BaseResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    class Meta:
        model = Site

    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        """Before importing sites that already exist, delete and import fresh."""
        if not dry_run:
            Site.objects.filter(id__in=dataset["id"]).delete()
