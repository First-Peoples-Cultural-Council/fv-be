from django.db.models import Prefetch
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models.galleries import Gallery, GalleryItem
from backend.serializers.gallery_serializers import (
    GalleryDetailSerializer,
    GallerySummarySerializer,
)
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from backend.views.utils import get_select_related_media_fields


@extend_schema_view(
    list=extend_schema(
        description="A list of galleries available on the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=GallerySummarySerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific gallery in the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=GalleryDetailSerializer,
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
        description="Create a new gallery for the site.",
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201,
                response=GalleryDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description="Update an existing gallery.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=GalleryDetailSerializer,
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
    partial_update=extend_schema(
        description="Update an existing gallery. Any omitted fields will be unchanged.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=GalleryDetailSerializer,
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
    destroy=extend_schema(
        description="Delete an existing gallery.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
)
class GalleryViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    """
    API endpoint that allows galleries to be viewed or edited.
    """

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Gallery.objects.filter(site=site)
            .order_by("title")
            .prefetch_related(
                "site",
                "site__language",
                Prefetch(
                    "galleryitem_set",
                    queryset=GalleryItem.objects.visible(
                        self.request.user
                    ).select_related(
                        *get_select_related_media_fields("image"),
                    ),
                ),
            )
            .select_related(
                "created_by",
                "last_modified_by",
                *get_select_related_media_fields("cover_image"),
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return GallerySummarySerializer
        return GalleryDetailSerializer
