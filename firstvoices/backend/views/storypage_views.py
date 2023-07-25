from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models import StoryPage
from backend.views.base_views import (
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    http_methods_except_patch,
)

from ..serializers.story_serializers import StoryPageSerializer
from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter


@extend_schema_view(
    list=extend_schema(
        description=_("A list of story pages associated with the specified site."),
        parameters=[site_slug_parameter],
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=StoryPageSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
    retrieve=extend_schema(
        description=_("Details about a specific story page."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=StoryPageSerializer,
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
        description=_("Add a story page."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=StoryPageSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description=_("Edit a story page."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=StoryPageSerializer,
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
        description=_("Delete a story page."),
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
class StoryPageViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    http_method_names = http_methods_except_patch

    def get_detail_queryset(self):
        site = self.get_validated_site()
        return StoryPage.objects.filter(site__slug=site[0].slug).all()

    def get_list_queryset(self):
        site = self.get_validated_site()
        return StoryPage.objects.filter(site__slug=site[0].slug).order_by("id").all()

    def get_serializer_class(self):
        return StoryPageSerializer
