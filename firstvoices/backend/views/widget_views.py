from django.db.models import Prefetch
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models.widget import SiteWidget, WidgetSettings
from backend.serializers.widget_serializers import SiteWidgetDetailSerializer
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import (
    FVPermissionViewSetMixin,
    SiteContentViewSetMixin,
    http_methods_except_patch,
)


@extend_schema_view(
    list=extend_schema(
        description="A list of available widgets for the specified site.",
        responses={
            200: SiteWidgetDetailSerializer,
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="A widget from the specified site.",
        responses={
            200: SiteWidgetDetailSerializer,
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description=_("Add a site widget."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=SiteWidgetDetailSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description=_("Edit a site widget."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=SiteWidgetDetailSerializer,
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
        description=_("Delete a site widget."),
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
class SiteWidgetViewSet(
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    http_method_names = http_methods_except_patch
    serializer_class = SiteWidgetDetailSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return (
                SiteWidget.objects.filter(site__slug=site[0].slug)
                .order_by("title")
                .prefetch_related(
                    Prefetch(
                        "widgetsettings_set",
                        queryset=WidgetSettings.objects.visible(self.request.user),
                    ),
                )
            )
        else:
            return SiteWidget.objects.none()
