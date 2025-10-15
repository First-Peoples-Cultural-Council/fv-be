from django.db.models.functions import Lower
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models.media import Person
from backend.serializers.media_serializers import PersonSerializer
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter


@extend_schema_view(
    list=extend_schema(
        description=_("A list of people associated with the specified site."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=PersonSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    retrieve=extend_schema(
        description=_("Details about a specific person."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=PersonSerializer,
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
        description=_("Add a person."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=PersonSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            site_slug_parameter,
            id_parameter,
        ],
    ),
    update=extend_schema(
        description=_("Edit a person."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=PersonSerializer,
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
        description=_("Edit a person. Any omitted fields will be unchanged."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=PersonSerializer,
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
        description=_("Delete a person."),
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
class PersonViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    serializer_class = PersonSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        return (
            Person.objects.filter(site=site)
            .annotate(name_lower=Lower("name"))
            .order_by("name_lower")
        )
