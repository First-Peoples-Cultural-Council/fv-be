from import_export.fields import Field
from import_export.results import RowResult
from import_export.widgets import ForeignKeyWidget

from backend.models.story import Story, StoryPage
from backend.resources.base import (
    ControlledSiteContentResource,
    RelatedMediaResourceMixin,
    SiteContentResource,
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


class StoryPageResource(SiteContentResource, RelatedMediaResourceMixin):
    story = Field(
        column_name="parent_id",
        attribute="story",
        widget=ForeignKeyWidget(Story, "id"),
    )
    notes = Field(
        column_name="notes",
        attribute="notes",
        widget=ArrayOfStringsWidget(sep="|||"),
    )

    class Meta:
        model = StoryPage

    def import_row(self, row, instance_loader, **kwargs):
        # overriding import_row to ignore errors and skip rows that fail to import without failing the entire import
        # ref: https://github.com/django-import-export/django-import-export/issues/763
        import_result = super().import_row(row, instance_loader, **kwargs)
        if (
            import_result.import_type == RowResult.IMPORT_TYPE_ERROR
            and type(import_result.errors[0].error) == Story.DoesNotExist
        ):
            # Copy the values to display in the preview report
            import_result.diff = [row[val] for val in row]
            # Add a column with the error message
            import_result.diff.append(
                f"Errors: {[err.error for err in import_result.errors]}"
            )
            # clear errors and mark the record to skip
            import_result.errors = []
            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result
