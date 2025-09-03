import io
import sys

from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import viewsets
from rest_framework.response import Response

from backend.models import DictionaryEntry
from backend.models.files import File
from backend.permissions.predicates import has_language_admin_membership, is_superadmin
from backend.permissions.utils import filter_by_viewable
from backend.serializers.dictionary_export_serializers import (
    DictionaryExportCsvSerializer,
)
from backend.utils.dictionary_export_utils import (
    FIELD_MAP,
    expand_many_to_one,
    get_dataset_from_queryset,
)
from backend.views.base_views import SiteContentViewSetMixin


class DictionaryExportViewSet(SiteContentViewSetMixin, viewsets.GenericViewSet):
    http_method_names = ["get"]

    def initial(self, *args, **kwargs):
        # Explicit method since we do not have a model attached,
        # thus, permissions would need to be checked manually
        super().initial(*args, **kwargs)

        if not self.request.user:
            return PermissionDenied

        # Check permission
        user = self.request.user
        site = self.get_validated_site()
        if not (has_language_admin_membership(user, site) or is_superadmin(user, site)):
            raise PermissionDenied

        return None

    def get_queryset(self):
        site = self.get_validated_site()
        queryset = DictionaryEntry.objects.filter(site=site)
        return filter_by_viewable(self.request.user, queryset)

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
            "RELATED_ENTRY_ID",
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
