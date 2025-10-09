from django.db.models import Prefetch
from django.db.models.functions import Lower
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models import SitePage
from backend.models.widget import SiteWidget
from backend.serializers.page_serializers import (
    SitePageDetailWriteSerializer,
    SitePageSerializer,
)
from backend.views import doc_strings
from backend.views.api_doc_variables import (
    inline_page_doc_detail_serializer,
    site_page_slug_parameter,
    site_slug_parameter,
)
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from backend.views.utils import get_select_related_media_fields


@extend_schema_view(
    list=extend_schema(
        description=_("A list of available pages for the specified site."),
        responses={
            200: SitePageSerializer,
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description=_("A page from the specified site."),
        responses={
            200: inline_page_doc_detail_serializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            site_page_slug_parameter,
        ],
    ),
    create=extend_schema(
        description=_("Add a page."),
        request=SitePageDetailWriteSerializer,
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201,
                response=inline_page_doc_detail_serializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description=_("Edit a page."),
        request=SitePageDetailWriteSerializer,
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=inline_page_doc_detail_serializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            site_page_slug_parameter,
        ],
    ),
    partial_update=extend_schema(
        description=_("Edit a page. Any omitted fields will be unchanged."),
        request=SitePageDetailWriteSerializer,
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=inline_page_doc_detail_serializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            site_page_slug_parameter,
        ],
    ),
    destroy=extend_schema(
        description=_("Delete a page."),
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
            site_page_slug_parameter,
        ],
    ),
)
class SitePageViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    lookup_field = "slug"
    serializer_class = SitePageDetailWriteSerializer

    def get_queryset(self):
        if self.action in ["retrieve", "update", "partial_update"]:
            return self.get_detail_queryset()

        site = self.get_validated_site()
        return (
            SitePage.objects.filter(site=site)
            .select_related(
                "widgets",
                "banner_image",
                "banner_video",
                "site",
                "site__language",
                "created_by",
                "last_modified_by",
            )
            .annotate(title_lower=Lower("title"))
            .order_by("title_lower")
        )

    def get_detail_queryset(self):
        site = self.get_validated_site()
        return (
            SitePage.objects.filter(site=site)
            .select_related(
                "widgets",
                "banner_image",
                "banner_video",
                "site",
                "site__language",
                "created_by",
                "last_modified_by",
                *get_select_related_media_fields("banner_image"),
                *get_select_related_media_fields("banner_video"),
            )
            .prefetch_related(
                Prefetch(
                    "widgets__widgets",
                    queryset=SiteWidget.objects.visible(self.request.user)
                    .select_related(
                        "site", "site__language", "created_by", "last_modified_by"
                    )
                    .prefetch_related("widgetsettings_set"),
                ),
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return SitePageSerializer
        else:
            return SitePageDetailWriteSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        site_widget_list = instance.widgets
        self.perform_destroy(instance)
        site_widget_list.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
