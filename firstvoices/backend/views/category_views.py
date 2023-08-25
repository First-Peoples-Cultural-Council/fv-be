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
from backend.search.utils.query_builder_utils import get_valid_boolean
from backend.serializers.category_serializers import (
    CategoryDetailSerializer,
    ParentCategoryFlatListSerializer,
    ParentCategoryListSerializer,
)
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter


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
            site_slug_parameter,
            OpenApiParameter(
                name="contains",
                description=_("Filter by type of dictionary entry associated with it"),
                deprecated=True,  # Contains flag will be removed eventually
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
            ),
            OpenApiParameter(
                name="nested",
                description=_(
                    "Returns a nested list of categories with their children if enabled"
                ),
                # If this parameter is true, ParentCategoryFlatListSerializer is used for the response
                default=True,
                required=False,
                type=bool,
                examples=[
                    OpenApiExample("True", value="True"),
                    OpenApiExample("False", value="False"),
                ],
            ),
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
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    create=extend_schema(
        description=_("Add a category."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=CategoryDetailSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
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
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    partial_update=extend_schema(
        description=_("Edit a category. Any omitted fields will be unchanged."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=CategoryDetailSerializer,
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
        description=_("Delete a category."),
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
class CategoryViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    valid_inputs = TypeOfDictionaryEntry.values

    def get_detail_queryset(self):
        site = self.get_validated_site()
        return (
            Category.objects.filter(site__slug=site[0].slug)
            .select_related("site", "created_by", "last_modified_by")
            .prefetch_related("children")
            .all()
        )

    def get_list_queryset(self):
        site = self.get_validated_site()
        list_queryset = Category.objects.filter(site__slug=site[0].slug)
        query = Q()

        # Check if type flags are present
        contains_flags = [
            flag.lower()
            for flag in self.request.GET.get("contains", "").split("|")
            if len(flag)
        ]

        # Check for the nested flag
        nested_flag_input = self.request.GET.get("nested", True)
        nested_flag = get_valid_boolean(nested_flag_input)

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
        child_queryset = Category.objects.filter(id__in=filtered_categories)

        if nested_flag:
            return filtered_categories.filter(
                ~Q(
                    id__in=flat_child_ids_list
                )  # Remove duplicate child entries being shown at top level
            ).prefetch_related(Prefetch("children", queryset=child_queryset))
        else:
            return filtered_categories.filter().prefetch_related(
                Prefetch("children", queryset=child_queryset)
            )

    def get_serializer_class(self):
        # Check for the nested flag
        nested_flag_input = self.request.GET.get("nested", True)
        nested_flag = get_valid_boolean(nested_flag_input)

        if self.action == "list" and nested_flag:
            serializer = ParentCategoryListSerializer
        elif self.action == "list" and not nested_flag:
            serializer = ParentCategoryFlatListSerializer
        else:
            serializer = CategoryDetailSerializer

        return serializer
