import io
import sys

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import viewsets
from rest_framework.response import Response

from backend.models import DictionaryEntry
from backend.models.files import File
from backend.serializers.dictionary_export_serializers import (
    DictionaryExportCsvSerializer,
)
from backend.utils.dictionary_export_utils import (
    FIELD_MAP,
    expand_many_to_one,
    get_dataset_from_queryset,
)
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


class DictionaryExportViewSet(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, viewsets.GenericViewSet
):
    def get_queryset(self):
        # todo: Filter queryset by user permissions
        site = self.get_validated_site()
        return DictionaryEntry.objects.filter(site=site)

    def list(self, request, *args, **kwargs):
        site = self.get_validated_site()
        queryset = self.get_queryset()

        dataset = get_dataset_from_queryset(queryset)
        dataset.headers = [FIELD_MAP.get(header, header) for header in dataset.headers]

        for field in [
            "TRANSLATION",
            "NOTE",
            "PRONUNCIATION",
            "ACKNOWLEDGEMENT",
            "ALTERNATE_SPELLING",
            "CATEGORY",
            "VIDEO_EMBED_LINK",
        ]:
            dataset = expand_many_to_one(dataset, field, max_columns=5)

        dataset_csv = dataset.export("csv")
        in_memory_csv = io.BytesIO(dataset_csv.encode("utf-8-sig"))
        in_memory_csv = InMemoryUploadedFile(
            file=in_memory_csv,
            field_name="dictionary_entries_export",
            name="dictionary_entries_export.csv",
            content_type="text/csv",
            size=sys.getsizeof(in_memory_csv),
            charset="utf-8",
        )
        csv_file = File(
            content=in_memory_csv,
            site=site,
            created_by=request.user,
            last_modified_by=request.user,
        )
        csv_file.save()

        return Response(DictionaryExportCsvSerializer(csv_file).data)
