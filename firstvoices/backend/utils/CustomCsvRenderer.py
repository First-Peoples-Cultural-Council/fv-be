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
        max_lengths = dict.fromkeys(fields, 0)
        for row in rows:
            for field in fields:
                num_values = len(row.get(field))
                max_lengths[field] = max(max_lengths[field], num_values)

        return max_lengths

    def get_first_seen_keys(self, rows):
        # To preserve order of headers in CSV
        seen = []
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    seen.append(k)
        return seen

    def expand_row(self, row, headers, flatten_fields, max_lengths):
        expanded_columns = {}

        for source_key, source_val in row.items():
            if source_key not in flatten_fields:
                # pass through if field does not require to be flattened
                expanded_columns[source_key] = "" if source_val is None else source_val
                continue

            base = flatten_fields[source_key]
            count = max(1, max_lengths.get(source_key, 0))

            # Padding if row contains values for a field less than the max_lengths
            # e.g. there are 3 max note columns for the CSV but an entry only contains 2 notes
            # the note_3 for that entry would be ""
            values = list(source_val)
            values = values + [""] * count

            # Filling values in expanded columns
            expanded_columns[base] = values[0]
            for i, value in enumerate(values[1:], start=2):
                expanded_columns[f"{base}_{i}"] = value

        return {header: expanded_columns.get(header, "") for header in headers}

    def render(self, data, accepted_media_type=None, renderer_context=None):
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
