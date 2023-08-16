from import_export import fields, resources, widgets

from backend.models.sites import Site
from backend.resources.utils.import_export_widgets import UserForeignKeyWidget


class BaseResource(resources.ModelResource):
    created_by = fields.Field(
        column_name="created_by",
        attribute="created_by",
        widget=UserForeignKeyWidget(),
    )
    last_modified_by = fields.Field(
        column_name="last_modified_by",
        attribute="last_modified_by",
        widget=UserForeignKeyWidget(),
    )

    class Meta:
        abstract = True


class SiteContentResource(BaseResource):
    site = fields.Field(
        column_name="site",
        attribute="site",
        widget=(widgets.ForeignKeyWidget(Site, "id")),
    )

    class Meta:
        abstract = True
