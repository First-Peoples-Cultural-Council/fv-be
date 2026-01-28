import csv
import io


def get_max_lengths(rows, fields):
    # Find max number of columns to add for flattened keys
    max_lengths = dict.fromkeys(fields, 0)
    for row in rows:
        for field in fields:
            num_values = len(row.get(field))
            max_lengths[field] = max(max_lengths[field], num_values)

    return max_lengths


def get_first_seen_keys(rows):
    # To preserve order of headers in CSV
    seen = []
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.append(k)
    return seen


def expand_row(row, headers, flatten_fields, max_lengths):
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


def convert_queryset_to_csv_content(data, flatten_fields=None):
    if flatten_fields is None:
        flatten_fields = {}
    # Compute max_lengths for flatten fields
    max_lengths = get_max_lengths(data, flatten_fields.keys())

    # Build headers
    base_order = get_first_seen_keys(data)  # to maintain order
    headers = []
    for key in base_order:
        if key in flatten_fields.keys():
            base = flatten_fields[key]
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
        writer.writerow(expand_row(row, headers, flatten_fields, max_lengths))

    output = buffer.getvalue()
    buffer.close()
    return output
