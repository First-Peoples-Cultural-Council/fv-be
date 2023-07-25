from django.db.models import Prefetch
from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models import SitePage
from backend.models.widget import SiteWidget
from backend.serializers.media_serializers import ImageSerializer, VideoSerializer
from backend.serializers.page_serializers import (
    SitePageDetailSerializer,
    SitePageDetailWriteSerializer,
    SitePageSerializer,
)
from backend.serializers.widget_serializers import SiteWidgetDetailSerializer
from backend.views import doc_strings
from backend.views.api_doc_variables import (
    site_page_slug_parameter,
    site_slug_parameter,
)
from backend.views.base_views import (
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    http_methods_except_patch,
)


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
            200: inline_serializer(
                name="InlinePageDetailSerializer",
                fields={
                    "id": serializers.UUIDField(),
                    "title": serializers.CharField(),
                    "url": serializers.URLField(),
                    "visibility": serializers.CharField(),
                    "subtitle": serializers.CharField(),
                    "slug": serializers.SlugField(),
                    "widgets": SiteWidgetDetailSerializer(many=True),
                    "banner_image": ImageSerializer(),
                    "banner_video": VideoSerializer(),
                },
            ),
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
                description=doc_strings.success_201, response=SitePageDetailSerializer
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
                response=SitePageDetailSerializer,
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
    http_method_names = http_methods_except_patch
    lookup_field = "slug"
    serializer_class = SitePageDetailWriteSerializer

    def get_queryset(self):
        if self.action == "retrieve":
            return self.get_detail_queryset()

        site = self.get_validated_site()
        return (
            SitePage.objects.filter(site__slug=site[0].slug)
            .select_related("widgets", "banner_image", "banner_video")
            .prefetch_related()
        )

    def get_detail_queryset(self):
        site = self.get_validated_site()
        return (
            SitePage.objects.filter(site__slug=site[0].slug)
            .select_related("widgets", "banner_image", "banner_video")
            .prefetch_related(
                Prefetch(
                    "widgets__widgets",
                    queryset=SiteWidget.objects.visible(self.request.user).order_by(
                        "sitewidgetlistorder_set__order"
                    ),
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
