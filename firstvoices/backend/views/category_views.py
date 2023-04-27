from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from backend.models.category import Category
from backend.serializers.category_serializers import CategoryListSerializer, CategoryDetailSerializer


@extend_schema_view(
    list=extend_schema(
        description="A list of categories associated with the specified site.",
        responses={
            200: CategoryListSerializer,
            403: OpenApiResponse(description="Todo: Not authorized for this Site."),
            404: OpenApiResponse(description="Todo: Site not found."),
        },
    ),
    retrieve=extend_schema(
        description="Details about a specific category.",
        responses={
            200: CategoryDetailSerializer,
            403: OpenApiResponse(description="Todo: Error Not Authorized"),
            404: OpenApiResponse(description="Todo: Not Found"),
        },
    )
)
class CategoryViewSet(
    FVPermissionViewSetMixin, SiteContentViewSetMixin, ModelViewSet
):
    http_method_names = ["get"]

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return Category.objects.filter(site__slug=site[0].slug).prefetch_related("children").all()
        else:
            return Category.objects.filter(site__slug=None)

    def get_list_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return Category.objects.filter(site__slug=site[0].slug).prefetch_related("children").exclude(
                parent__isnull=False
            )
        else:
            return Category.objects.filter(site__slug=None).prefetch_related("children").exclude(
                parent__isnull=False
            )

    def get_serializer_class(self):
        if self.action == "list":
            return CategoryListSerializer
        if self.action == "retrieve":
            return CategoryDetailSerializer
        return CategoryListSerializer
