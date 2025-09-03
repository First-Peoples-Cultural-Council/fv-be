import io
import sys

import tablib
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.related import ManyToManyField
from rest_framework import viewsets
from rest_framework.response import Response

from backend.models import DictionaryEntry
from backend.models.files import File
from backend.serializers.dictionary_export_serializers import (
    DictionaryExportCsvSerializer,
)
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

field_map = {
    "id": "ID",
    "title": "TITLE",
    "type": "TYPE",
    "translations": "TRANSLATION",
    "categories": "CATEGORY",
    "visibility": "VISIBILITY",
    "part_of_speech": "PART_OF_SPEECH",
}


def get_dataset_from_queryset(queryset, site, request):
    # Convert to CSV
    fields = [
        "id",
        "title",
        "type",
        "translations",
        "categories",
        "visibility",
        "part_of_speech",
        "exclude_from_games",
        "exclude_from_kids",
        "related_video_links",
        "notes",
        "acknowledgements",
        "alternate_spellings",
        "pronunciations",
    ]

    headers = fields
    data = []

    for obj in queryset:
        row = []
        for field in fields:
            dictionary_entry_field = DictionaryEntry._meta.get_field(field)

            # many to many fields
            if isinstance(dictionary_entry_field, ManyToManyField):
                values = getattr(obj, field).all()
                values = [str(value) for value in values]
                row.append(values)
            else:
                value = getattr(obj, field)

                # field with choices
                if hasattr(obj, f"get_{field}_display"):
                    value = getattr(obj, f"get_{field}_display")()
                row.append(value)
        data.append(row)

    dataset = tablib.Dataset(*data, headers=headers)
    return dataset


def expand_many_to_one(dataset, field_name, max_columns=None):
    if field_name not in dataset.headers:
        return dataset

    field_index = dataset.headers.index(field_name)

    # determine max columns
    actual_max = 0
    for row in dataset.dict:
        value = row.get(field_name, [])
        if isinstance(value, (list, tuple)):
            actual_max = max(actual_max, len(value))
        elif value:
            actual_max = max(actual_max, 1)

    # final columns
    num_columns = actual_max if max_columns is None else min(actual_max, max_columns)

    new_headers = (
        dataset.headers[:field_index]
        + [
            field_name if i == 0 else f"{field_name}_{i + 1}"
            for i in range(num_columns)
        ]
        + dataset.headers[field_index + 1 :]  # noqa: E203
    )

    # build new rows
    new_data = []
    for row in dataset.dict:
        values = row.get(field_name, [])
        if not isinstance(values, (list, tuple)):
            values = [values] if values else []

        expanded_values = [
            values[i] if i < len(values) else "" for i in range(num_columns)
        ]

        before = [row[h] for h in dataset.headers[:field_index]]
        after = [row[h] for h in dataset.headers[field_index + 1 :]]  # noqa: E203
        new_row = before + expanded_values + after
        new_data.append(new_row)

    return tablib.Dataset(*new_data, headers=new_headers)


class DictionaryExportViewSet(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, viewsets.GenericViewSet
):
    def get_queryset(self):
        site = self.get_validated_site()
        return DictionaryEntry.objects.filter(site=site)

    def list(self, request, *args, **kwargs):
        site = self.get_validated_site()
        queryset = self.get_queryset()

        exported_entries_dataset = get_dataset_from_queryset(queryset, site, request)
        new_headers = [
            field_map.get(header, header) for header in exported_entries_dataset.headers
        ]
        exported_entries_dataset.headers = new_headers

        # Expanding datasets for all fields
        exported_entries_dataset = expand_many_to_one(
            exported_entries_dataset, "TRANSLATION", max_columns=5
        )
        exported_entries_dataset = expand_many_to_one(
            exported_entries_dataset, "CATEGORY", max_columns=5
        )

        dataset_csv_export = exported_entries_dataset.export("csv")
        in_memory_csv_file = io.BytesIO(dataset_csv_export.encode("utf-8-sig"))
        in_memory_csv_file = InMemoryUploadedFile(
            file=in_memory_csv_file,
            field_name="dictionary_entries_export",
            name="dictionary_entries_export.csv",
            content_type="text/csv",
            size=sys.getsizeof(in_memory_csv_file),
            charset="utf-8",
        )
        csv_file = File(
            content=in_memory_csv_file,
            site=site,
            created_by=request.user,
            last_modified_by=request.user,
        )
        csv_file.save()

        serializer = DictionaryExportCsvSerializer(csv_file)
        return Response(serializer.data)
