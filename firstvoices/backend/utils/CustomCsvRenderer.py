from rest_framework.renderers import BaseRenderer

from backend.utils.export_utils import convert_queryset_to_csv_content


class CustomCsvRenderer(BaseRenderer):
    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    flatten_fields = {}

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Get flatten fields from the view if present
        view = (renderer_context or {}).get("view")
        self.flatten_fields = getattr(view, "flatten_fields", self.flatten_fields)

        output = convert_queryset_to_csv_content(
            data, flatten_fields=self.flatten_fields
        )
        return output
