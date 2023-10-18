from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from datetime import datetime

from backend.models import Membership
from backend.models.constants import Role
from backend.models.join_request import JoinRequest, JoinRequestStatus
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
    create=extend_schema(
        description=_("Create a join request."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201,
                response=JoinRequestDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
    destroy=extend_schema(
        description=_("Delete a join request."),
        responses={
            204: OpenApiResponse(
                description=doc_strings.success_204_deleted,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
)
class JoinRequestViewSet(
    SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet
):
    """
    API endpoint for managing join requests.
    """

    serializer_class = JoinRequestDetailSerializer
    http_method_names = ["get", "post", "delete"]

    permission_type_map = {
        "create": "add",
        "destroy": "delete",
        "list": None,
        "partial_update": "change",
        "retrieve": "view",
        "update": "change",

        "approve": "change",  # custom actions use change permission
        "ignore": "change",
        "reject": "change",
    }

    def get_queryset(self):
        site = self.get_validated_site()
        if site.count() > 0:
            return JoinRequest.objects.filter(site__slug=site[0].slug).select_related(
                "site", "site__language", "created_by", "last_modified_by", "user"
            )
        else:
            return JoinRequest.objects.none()

    @action(detail=True, methods=['post'])
    def ignore(self, request, site_slug=None, pk=None):
        site = self.get_validated_site().first()
        join_request = self.get_validated_join_request(site, pk)

        self.update_join_request_status(join_request, JoinRequestStatus.IGNORED, request.user)

        serializer = self.get_serializer(join_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def reject(self, request, site_slug=None, pk=None):
        site = self.get_validated_site().first()
        join_request = self.get_validated_join_request(site, pk)

        self.update_join_request_status(join_request, JoinRequestStatus.REJECTED, request.user)

        # notify user here, see FW-5077

        serializer = self.get_serializer(join_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def approve(self, request, site_slug=None, pk=None):
        site = self.get_validated_site().first()

        if "role" not in request.data:
            raise ValidationError({"role": [
                "This field is required."
            ]})

        try:
            role_value = request.data["role"]
            role = Role[role_value.upper()]
        except KeyError:
            raise ValidationError({"role": ["value must be one of: " + ", ".join(Role.names)]})

        join_request = self.get_validated_join_request(site, pk)
        user = join_request.user

        has_membership = Membership.objects.filter(site=site, user=user).first()
        if has_membership:
            raise ValidationError("User already has a membership on this site")

        with transaction.atomic():
            Membership.objects.create(user=user, site=site, role=role)
            self.update_join_request_status(join_request, JoinRequestStatus.APPROVED, request.user)

        # notify user here, see FW-5077

        serializer = self.get_serializer(join_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_validated_join_request(self, site, pk):
        try:
            join_requests = JoinRequest.objects.filter(pk=pk, site=site)
        except ValidationError:
            # pk is not a valid uuid
            raise Http404

        if len(join_requests) == 0:
            raise Http404

        # Check join request change permissions
        perm = JoinRequest.get_perm("change")
        jr = join_requests.first()
        if not self.request.user.has_perm(perm, jr):
            raise PermissionDenied
        else:
            return jr

    def update_join_request_status(self, join_request, status, user):
        join_request.status = status
        join_request.last_modified_by = user
        join_request.last_modified = datetime.now()
        join_request.save()
