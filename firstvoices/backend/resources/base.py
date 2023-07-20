from import_export import fields, resources

from backend.resources.utils.import_export_widgets import UserForeignKeyWidget


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
