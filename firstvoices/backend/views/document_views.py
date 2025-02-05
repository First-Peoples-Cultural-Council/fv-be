from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import parsers, viewsets

from backend.models.media import Document
from backend.serializers.media_detail_serializers import DocumentDetailSerializer
from backend.serializers.media_serializers import DocumentSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter


@extend_schema_view(
    list=extend_schema(
        description=_("A list of available documents for the specified site."),
        responses={
            200: DocumentSerializer,
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description=_("A document item from the specified site."),
        responses={
            200: DocumentSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description=_(
            "Add a document item. The 'original' field would not work with the 'application/json' content-type."
        ),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=DocumentSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    destroy=extend_schema(
        description=_("Delete a document item."),
        responses={
            204: OpenApiResponse(
                description=doc_strings.success_204_deleted,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class DocumentViewSet(
    SiteContentViewSetMixin,
    FVPermissionViewSetMixin,
    viewsets.ModelViewSet,
):
    """
    Document information.
    """

    serializer_class = DocumentSerializer
    parser_classes = [
        parsers.FormParser,
        parsers.MultiPartParser,
    ]  # to support file uploads

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Document.objects.filter(site=site)
            .prefetch_related("original", "site")
            .order_by("-created")
            .defer(
                "created_by_id",
                "last_modified_by_id",
                "last_modified",
            )
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DocumentDetailSerializer
        return DocumentSerializer
