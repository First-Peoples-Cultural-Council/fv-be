import itertools

from django.db.models import Prefetch, Q
from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework.viewsets import ModelViewSet

from backend.models.category import Category
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.serializers.category_serializers import (
    CategoryDetailSerializer,
    ParentCategoryListSerializer,
)
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings


@extend_schema_view(
    list=extend_schema(
        description=_("A list of categories associated with the specified site."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=ParentCategoryListSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            OpenApiParameter(
                name="contains",
                description=_("Filter by type of dictionary entry associated with it"),
                required=False,
                type=str,
                examples=[
                    OpenApiExample("WORD", value="WORD"),
                    OpenApiExample("PHRASE", value="PHRASE"),
                    OpenApiExample(
                        "WORD|PHRASE",
                        value="WORD|PHRASE",
                        description=_(
                            "Contains any of the specified types. Order is not relevant."
                        ),
                    ),
                ],
            )
        ],
    ),
    retrieve=extend_schema(
        description=_("Details about a specific category."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=CategoryDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
    update=extend_schema(
        description=_("Edit a category."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=CategoryDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
    destroy=extend_schema(
        description=_("Delete a category."),
        responses={
            204: OpenApiResponse(
                description=doc_strings.success_204_deleted,
                response=CategoryDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
)
class CategoryViewSet(FVPermissionViewSetMixin, SiteContentViewSetMixin, ModelViewSet):
    http_method_names = ["get", "put", "delete"]
    valid_inputs = TypeOfDictionaryEntry.values

    def get_detail_queryset(self):
        site = self.get_validated_site()
        return (
            Category.objects.filter(site__slug=site[0].slug)
            .prefetch_related("children")
            .all()
        )

    def get_list_queryset(self):
        site = self.get_validated_site()
        list_queryset = Category.objects.filter(site__slug=site[0].slug)
        query = Q()

        # Check if type flags are present
        contains_flags = [
            flag.upper()
            for flag in self.request.GET.get("contains", "").split("|")
            if len(flag)
        ]

        if len(contains_flags) > 0:
            for flag in contains_flags:
                # Check if flag is in valid_inputs and then add
                if flag in self.valid_inputs:
                    query.add(Q(dictionary_entries__type=flag), Q.OR)
            if len(query) == 0:  # Only invalid flags were supplied
                return Category.objects.none()

        filtered_categories = (
            list_queryset.filter(query).order_by("id").distinct("id")
        )  # Relevant categories which satisfy the query
        child_categories = [
            category.children.all().values_list("id", flat=True)
            for category in filtered_categories
            if len(category.children.all())
        ]
        flat_child_ids_list = list(itertools.chain(*child_categories))

        return filtered_categories.filter(
            ~Q(
                id__in=flat_child_ids_list
            )  # Remove duplicate child entries being shown at top level
        ).prefetch_related(
            Prefetch(
                "children",
                queryset=Category.objects.filter(id__in=filtered_categories),
            )  # Filter child categories
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ParentCategoryListSerializer
        else:
            return CategoryDetailSerializer
