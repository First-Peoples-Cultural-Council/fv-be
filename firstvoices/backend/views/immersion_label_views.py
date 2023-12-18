from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models.immersion_labels import ImmersionLabel
from backend.permissions.utils import filter_by_viewable
from backend.serializers.immersion_label_serializers import (
    ImmersionLabelDetailSerializer,
)
from backend.views import doc_strings
from backend.views.api_doc_variables import key_parameter, site_slug_parameter
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of immersion labels available on the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=ImmersionLabelDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description="Details about a specific immersion label in the specified site.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=ImmersionLabelDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            key_parameter,
        ],
    ),
    create=extend_schema(
        description="Create a new immersion label for the site. Immersion label keys cannot be changed after creation.",
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201,
                response=ImmersionLabelDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description="Edit an immersion label in the site. Immersion label keys cannot be changed after creation.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=ImmersionLabelDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            key_parameter,
        ],
    ),
    partial_update=extend_schema(
        description="Edit an immersion label in the specified site. Any omitted fields will be unchanged.",
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=ImmersionLabelDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[
            site_slug_parameter,
            key_parameter,
        ],
    ),
    destroy=extend_schema(
        description="Delete an immersion label from the specified site.",
        responses={
            204: OpenApiResponse(description=doc_strings.success_204_deleted),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[site_slug_parameter, key_parameter],
    ),
    all=extend_schema(
        description="Returns a mapping of immersion label keys to their corresponding dictionary entry titles.",
        responses={
            200: inline_serializer(
                name="ImmersionLabelMap",
                fields={
                    "key": serializers.CharField(),
                    "dictionary_entry_title": serializers.CharField(),
                },
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
)
class ImmersionLabelViewSet(
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    """
    API endpoint that allows immersion labels to be viewed and edited.
    """

    lookup_field = "key"
    serializer_class = ImmersionLabelDetailSerializer
    permission_type_map = {
        **FVPermissionViewSetMixin.permission_type_map,
        "all": None,
    }

    def get_queryset(self):
        site = self.get_validated_site()
        return ImmersionLabel.objects.filter(site__slug=site[0].slug).select_related(
            "site",
            "site__language",
            "created_by",
            "last_modified_by",
            "dictionary_entry",
        )

    @action(detail=False, methods=["get"])
    def all(self, request, *args, **kwargs):
        """
        Returns a mapping of immersion label keys to their corresponding dictionary entry titles.
        """
        immersion_labels = filter_by_viewable(request.user, self.get_queryset())

        immersion_labels_map = {
            label.key: label.dictionary_entry.title for label in immersion_labels
        }

        return Response(immersion_labels_map)
