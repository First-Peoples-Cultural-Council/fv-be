from django.db import transaction
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework.viewsets import ModelViewSet

from backend.models.jobs import ExportJob, JobStatus
from backend.search.constants import TYPE_PHRASE, TYPE_WORD
from backend.search.utils import get_site_entries_search_params
from backend.serializers.export_job_serializers import ExportJobSerializer
from backend.serializers.export_serializers import DictionaryEntryExportSerializer
from backend.tasks.export_job_tasks import generate_export_csv
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_search_entries_views import BASE_SEARCH_PARAMS
from backend.views.base_views import (
    AsyncJobDeleteMixin,
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
)
from backend.views.search_site_entries_views import SITE_SEARCH_PARAMS
from firstvoices.celery import link_error_handler


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
    AsyncJobDeleteMixin,
    SiteContentViewSetMixin,
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
    started_statuses = [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE]

    def get_queryset(self):
        site = self.get_validated_site()
        return ExportJob.objects.filter(site=site).order_by("-created")

    def perform_create(self, serializer):
        site = self.get_validated_site()
        search_params = get_site_entries_search_params(
            self.request, site, self.default_search_types, self.allowed_search_types
        )

        export_params = search_params.copy()
        key_to_remove = "user"
        if key_to_remove in export_params:
            del export_params[key_to_remove]

        export_job_instance = serializer.save(export_params=export_params)
        export_job_instance.status = JobStatus.ACCEPTED
        export_job_instance.save()
        export_job_id = export_job_instance.id

        # Trigger the search and export csv generation after model creation
        transaction.on_commit(
            lambda: generate_export_csv.apply_async(
                (str(export_job_id),),
                link_error=link_error_handler.s(),
                ignore_result=True,
            )
        )
