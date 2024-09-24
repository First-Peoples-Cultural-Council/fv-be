from django.db.models import Prefetch
from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework.viewsets import ModelViewSet

from backend.models import Story, StoryPage
from backend.serializers.story_serializers import (
    StoryDetailUpdateSerializer,
    StoryListSerializer,
    StorySerializer,
)
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter
from .utils import get_created_ordered_media_prefetch_list, get_media_prefetch_list


@extend_schema_view(
    list=extend_schema(
        description=_("A list of stories associated with the specified site."),
        parameters=[
            site_slug_parameter,
            OpenApiParameter(
                "detail",
                OpenApiTypes.BOOL,
                OpenApiParameter.QUERY,
                default="false",
                description="return all page data associated with a story.",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=StoryListSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
    retrieve=extend_schema(
        description=_("Details about a specific story."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=StorySerializer,
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
        description=_("Add a story."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=StorySerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description=_("Edit a story."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=StorySerializer,
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
        description=_("Edit a story. Any omitted fields will be unchanged."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=StorySerializer,
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
        description=_("Delete a story."),
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
class StoryViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    def get_detail_queryset(self):
        site = self.get_validated_site()
        return (
            Story.objects.filter(site=site)
            .select_related("site", "site__language", "created_by", "last_modified_by")
            .prefetch_related(
                *get_media_prefetch_list(self.request.user),
                Prefetch(
                    "pages",
                    queryset=StoryPage.objects.filter(site=site)
                    .order_by("ordering")
                    .select_related(
                        "site", "site__language", "created_by", "last_modified_by"
                    )
                    .prefetch_related(
                        *get_created_ordered_media_prefetch_list(self.request.user)
                    ),
                )
            )
        )

    def get_list_queryset(self):
        site = self.get_validated_site()
        return (
            Story.objects.filter(site=site)
            .order_by("title")
            .select_related("site", "site__language", "created_by", "last_modified_by")
            .prefetch_related(
                *get_media_prefetch_list(self.request.user),
                Prefetch(
                    "pages",
                    queryset=StoryPage.objects.filter(site=site)
                    .order_by("ordering")
                    .select_related(
                        "site", "site__language", "created_by", "last_modified_by"
                    )
                    .prefetch_related(
                        *get_created_ordered_media_prefetch_list(self.request.user)
                    ),
                )
            )
        )

    def get_serializer_class(self):
        if self.action in ("list",):
            if self.request.query_params.get("detail", "false").lower() in ("true",):
                return StorySerializer
            return StoryListSerializer
        elif self.action in ("update", "partial_update"):
            return StoryDetailUpdateSerializer
        else:
            return StorySerializer
