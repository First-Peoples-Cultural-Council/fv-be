from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework.viewsets import ModelViewSet

from backend.models.files import File
from backend.models.jobs import ExportJob, JobStatus
from backend.search.constants import TYPE_PHRASE, TYPE_WORD
from backend.search.queries.query_builder import (
    get_base_entries_search_query,
    get_base_entries_sort_query,
)
from backend.search.utils import get_search_response, get_site_entries_search_params
from backend.serializers.export_job_serializers import ExportJobSerializer
from backend.serializers.export_serializers import DictionaryEntryExportSerializer
from backend.utils.export_utils import convert_queryset_to_csv_content
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_search_entries_views import BASE_SEARCH_PARAMS
from backend.views.base_search_views import HydrateSerializeSearchResultsMixin
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from backend.views.search_site_entries_views import SITE_SEARCH_PARAMS


@extend_schema_view(
    list=extend_schema(
        description="A list of all export jobs for the specified site.",
        responses={
            200: ExportJobSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific export job.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=ExportJobSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description="Creates a new export job. The job can be validated or confirmed using the relevant endpoints.",
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=ExportJobSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            *SITE_SEARCH_PARAMS,
            *BASE_SEARCH_PARAMS,
            OpenApiParameter(
                name="types",
                description="Filter by type of content. Options are word & phrase.",
                required=False,
                default="",
                type=str,
                examples=[
                    OpenApiExample(
                        "",
                        value="",
                        description="Retrieves all types of results.",
                    ),
                    OpenApiExample(
                        "word",
                        value="word",
                        description="Retrieves all words.",
                    ),
                    OpenApiExample(
                        "phrase",
                        value="phrase",
                        description="Retrieves all phrases.",
                    ),
                ],
            ),
        ],
    ),
    destroy=extend_schema(
        description="Deletes a single export-job and its associated file for the specified site. ",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class ExportJobViewSet(
    SiteContentViewSetMixin,
    HydrateSerializeSearchResultsMixin,
    FVPermissionViewSetMixin,
    ModelViewSet,
):
    """
    API endpoint that allows export jobs to be viewed.
    """

    http_method_names = ["get", "post", "delete"]
    serializer_class = ExportJobSerializer
    serializer_classes = {
        "DictionaryEntry": DictionaryEntryExportSerializer,
    }
    default_search_types = [TYPE_WORD, TYPE_PHRASE]
    allowed_search_types = [TYPE_WORD, TYPE_PHRASE]
    flatten_fields = {
        "categories": "category",
        "translations": "translation",
        "notes": "note",
        "acknowledgements": "acknowledgement",
        "alternate_spellings": "alternate_spelling",
        "pronunciations": "pronunciation",
        "related_dictionary_entries": "related_entry_id",
    }

    def get_queryset(self):
        site = self.get_validated_site()
        return ExportJob.objects.filter(site=site).order_by("-created")

    def perform_create(self, serializer):
        export_job_instance = serializer.save()
        export_job_instance.status = JobStatus.ACCEPTED
        export_job_instance.save()

        # Trigger the search and export csv generation after model creation
        transaction.on_commit(lambda: self.generate_export(export_job_instance))

    def generate_export(self, export_job_instance):
        site = self.get_validated_site()
        filename = f"export_{site.slug}_{timezone.localtime(timezone.now()).strftime("%Y_%m_%d_%H_%M_%S")}.csv"

        results = self.get_search_results()

        export_job_instance.status = JobStatus.STARTED
        export_job_instance.save()

        csv_string = convert_queryset_to_csv_content(results, self.flatten_fields)
        csv_file_content = ContentFile(csv_string, filename)
        export_csv_file = File(
            content=csv_file_content,
            site=site,
            created_by=export_job_instance.last_modified_by,
            last_modified_by=export_job_instance.last_modified_by,
        )
        export_csv_file.save()

        export_job_instance.export_csv = export_csv_file
        export_job_instance.status = JobStatus.COMPLETE
        export_job_instance.save()

        return export_job_instance.id

    def get_search_results(self):
        site = self.get_validated_site()

        search_params = get_site_entries_search_params(
            self.request, site, self.default_search_types, self.allowed_search_types
        )

        search_query = get_base_entries_search_query(**search_params)
        search_query = get_base_entries_sort_query(search_query, **search_params)

        response = get_search_response(search_query)
        search_results = response["hits"]["hits"]

        data = self.hydrate(search_results)
        serialized_data = self.serialize_search_results(
            search_results, data, **search_params
        )
        serialized_data = [
            dictionary_entry["entry"] for dictionary_entry in serialized_data
        ]

        return serialized_data

    def get_data_to_serialize(self, result, data):
        entry_data = super().get_data_to_serialize(result, data)
        if entry_data is None:
            return None

        return {"search_result_id": result["_id"], "entry": entry_data}

    def make_queryset_eager(self, model_name, queryset):
        """Custom method to pass the user to serializers, to allow for permission-based prefetching.

        Returns: updated queryset
        """
        serializer = self.get_serializer_class_for_model_type(model_name)
        if hasattr(serializer, "make_queryset_eager"):
            return serializer.make_queryset_eager(queryset, self.request.user)
        else:
            return queryset
