from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from backend.models.join_request import JoinRequest
from backend.serializers.join_request_serializers import JoinRequestDetailSerializer
from backend.views import doc_strings
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description=_("A list of join requests associated with the specified site."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=JoinRequestDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
    retrieve=extend_schema(
        description=_("Details about a specific join request."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=JoinRequestDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
)
class JoinRequestViewSet(
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    """
    API endpoint that allows join requests to be viewed or edited.
    """

    http_method_names = ["get"]

    serializer_class = JoinRequestDetailSerializer

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return JoinRequest.objects.filter(site__slug=site[0].slug).select_related(
                "site", "site__language", "created_by", "last_modified_by", "user"
            )
        else:
            return JoinRequest.objects.none()
