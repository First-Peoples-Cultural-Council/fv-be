from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from backend.models.sites import Site
from backend.models.user import User

base_fields = ["created", "created_by", "last_modified", "last_modified_by"]


class SiteResource(resources.ModelResource):
    created_by = fields.Field(
        column_name="created_by",
        attribute="created_by",
        widget=ForeignKeyWidget(User, field="email"),
    )
    last_modified_by = fields.Field(
        column_name="last_modified_by",
        attribute="last_modified_by",
        widget=ForeignKeyWidget(User, field="email"),
    )
    # TODO: check timezone on import/export
    # TODO: see if these can subclass into "baseresource"

    class Meta:
        model = Site
        fields = (
            *base_fields,
            *(
                "id",
                "slug",
                "title",
                "language",
                "language__title",
                "contact_email",
                "visibility",
            ),
        )
        export_order = (
            "id",
            "slug",
            "title",
            "visibility",
            "contact_email",
            "language__title",
        )
