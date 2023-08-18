from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models.constants import Visibility
from backend.models.widget import SiteWidget, WidgetFormats, WidgetSettings
from backend.resources.base import BaseResource, SiteContentResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class SiteWidgetResource(SiteContentResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    format = fields.Field(
        column_name="format",
        widget=ChoicesWidget(WidgetFormats.choices),
        attribute="format",
    )

    class Meta:
        model = SiteWidget


class WidgetSettingsResource(BaseResource):
    widget = fields.Field(
        column_name="widget_id",
        attribute="widget",
        widget=ForeignKeyWidget(SiteWidget, "id"),
    )

    class Meta:
        model = WidgetSettings
