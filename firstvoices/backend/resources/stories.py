from import_export.fields import Field

from backend.models.story import Story
from backend.resources.base import (
    ControlledSiteContentResource,
    RelatedMediaResourceMixin,
)
from backend.resources.utils.import_export_widgets import ArrayOfStringsWidget


class StoryResource(ControlledSiteContentResource, RelatedMediaResourceMixin):
    acknowledgements = Field(
        column_name="acknowledgements",
        attribute="acknowledgements",
        widget=ArrayOfStringsWidget(sep="|||"),
    )
    notes = Field(
        column_name="notes",
        attribute="notes",
        widget=ArrayOfStringsWidget(sep="|||"),
    )

    class Meta:
        model = Story
