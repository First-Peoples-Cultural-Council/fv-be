import csv
import io

from rest_framework.renderers import BaseRenderer


class CustomCsvRenderer(BaseRenderer):
    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    flatten_fields = {}

    def get_max_lengths(self, rows, fields):
        # Find max number of columns to add for flattened keys
        max_lengths = {field: 0 for field in fields}
        for r in rows:
            for f in fields:
                value = r.get(f)
                if isinstance(value, (list, tuple)):
                    max_lengths[f] = max(max_lengths[f], len(value))
                else:
                    max_lengths[f] = max(max_lengths[f], 1)

        return max_lengths

    def get_first_seen_keys(self, rows):
        # To preserve order of headers in CSV
        seen = []
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    seen.append(k)
        return seen

    def normalize_value_to_list(self, value):
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    def expand_row(self, row, headers, flatten_fields, max_lengths):
        expanded_columns = {}

        for source_key, source_val in row.items():
            if source_key in flatten_fields:
                base_col_name = flatten_fields[source_key]
                num_columns = max(1, max_lengths.get(source_key, 0))
                values_list = self.normalize_value_to_list(source_val)

                # First column uses base name, rest are suffixed
                for i in range(num_columns):
                    col_name = base_col_name if i == 0 else f"{base_col_name}_{i+1}"
                    expanded_columns[col_name] = (
                        values_list[i] if i < len(values_list) else ""
                    )
            else:
                expanded_columns[source_key] = "" if source_val is None else source_val

        return {header: expanded_columns.get(header, "") for header in headers}

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return ""

        # Get flatten fields from the view if present
        view = (renderer_context or {}).get("view")
        self.flatten_fields = getattr(view, "flatten_fields", self.flatten_fields)

        # Compute max_lengths for flatten fields
        max_lengths = self.get_max_lengths(data, self.flatten_fields.keys())

        # Build headers
        base_order = self.get_first_seen_keys(data)  # to maintain order
        headers = []
        for key in base_order:
            if key in self.flatten_fields.keys():
                base = self.flatten_fields[key]
                n = max(1, max_lengths.get(key, 0))
                for i in range(n):
                    headers.append(base if i == 0 else f"{base}_{i+1}")
            else:
                headers.append(key)

        # Build CSV
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(
                self.expand_row(row, headers, self.flatten_fields, max_lengths)
            )

        output = buffer.getvalue()
        buffer.close()
        return output
