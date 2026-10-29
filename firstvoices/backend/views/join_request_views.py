import logging
from datetime import datetime

import redis.exceptions
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.models import Membership, Site
from backend.models.constants import Role
from backend.models.join_request import JoinRequest, JoinRequestStatus
from backend.search.validators import get_valid_boolean
from backend.serializers import fields
from backend.serializers.join_request_serializers import JoinRequestDetailSerializer
from backend.tasks.send_email_tasks import send_email_task
from backend.views import doc_strings
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin
from backend.views.utils import (
    get_site_content_select_related_fields,
    get_site_url_from_appjson,
)


@extend_schema_view(
    list=extend_schema(
        description=_(
            "A list of pending join requests associated with the specified site."
        ),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=JoinRequestDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[
            OpenApiParameter(
                name="myRequests",
                description=_(
                    "Filter to only show join requests made by the current user."
                ),
                required=False,
                type=bool,
                examples=[
                    OpenApiExample("True", value=True),
                    OpenApiExample("False", value=False),
                ],
            )
        ],
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
    approve=extend_schema(
        description=_(
            "Approve a join request, and create a corresponding site membership."
        ),
        request=inline_serializer(
            name="Join Request Approval",
            fields={"role": fields.EnumLabelField(enum=Role)},
        ),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=JoinRequestDetailSerializer,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
    ignore=extend_schema(
        description=_("Ignore a join request."),
        request=inline_serializer(name="Join Request Ignore", fields={}),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
    ),
    reject=extend_schema(
        description=_("Reject a join request."),
        request=inline_serializer(name="Join Request Rejection", fields={}),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
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

    def get_detail_queryset(self):
        site = self.get_validated_site()
        return JoinRequest.objects.filter(
            site=site, status=JoinRequestStatus.PENDING
        ).select_related(*get_site_content_select_related_fields(), "user")

    def get_list_queryset(self):
        site = self.get_validated_site()
        queryset = JoinRequest.objects.filter(site=site)

        if not self.request.user.is_authenticated:
            return queryset.none()

        my_requests = self.is_my_requests_query()
        if my_requests:
            queryset = queryset.filter(user=self.request.user)
        else:
            queryset = queryset.filter(status=JoinRequestStatus.PENDING)
            # Exclude the current user's join requests from the list if not filtering for "myRequests"
            queryset = queryset.exclude(user=self.request.user)

        return queryset.order_by("-created").select_related(
            *get_site_content_select_related_fields(), "user"
        )

    def is_my_requests_query(self):
        return get_valid_boolean(self.request.query_params.get("myRequests", False))

    def get_validated_site(self):
        if self.action != "create" and not self.is_my_requests_query():
            return super().get_validated_site()

        # Special case to allow creating a join request for any site that exists
        # also allows non-admin users to view their own join requests for sites they don't have access to
        site_slug = self.get_site_slug()
        sites = Site.objects.filter(slug=site_slug)

        if not sites.exists():
            raise Http404

        return sites.first()

    def list(self, request, *args, **kwargs):
        # If the "myRequests" query parameter is set, ignore the view permission filter
        if not self.is_my_requests_query():
            return super().list(request, *args, **kwargs)

        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(page, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def ignore(self, request, site_slug=None, pk=None):
        join_request = self.get_object()

        self.update_join_request_status(
            join_request, JoinRequestStatus.IGNORED, request.user
        )

        serializer = self.get_serializer(join_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reject(self, request, site_slug=None, pk=None):
        join_request = self.get_object()

        self.update_join_request_status(
            join_request, JoinRequestStatus.REJECTED, request.user
        )

        subject = (
            f"Update on your request to join {join_request.site.title} on FirstVoices"
        )
        message = (
            f"Thank you for requesting to join the {join_request.site.title} site on FirstVoices. "
            "A community administrator has reviewed your request. At this time, your request to view private content "
            "has not been approved. The site may not be accepting members at this time.\n\n"
            "Your request may be re-reviewed at a later date.\n\n"
            "All decisions regarding requests to view private content are made solely by community-based language "
            "administrators.\n\n"
            "If you think this may be a technical error, you can contact FirstVoices staff at "
            "hello@firstvoices.com.\n\n"
        )

        try:
            send_email_task.apply_async((subject, message, [join_request.user.email]))
        except redis.exceptions.ConnectionError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Could not queue task. Error: {e}")

        serializer = self.get_serializer(join_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def approve(self, request, site_slug=None, pk=None):
        if "role" not in request.data:
            raise ValidationError({"role": ["This field is required."]})

        try:
            role_value = request.data["role"]
            role = Role[role_value.upper()]
        except KeyError:
            raise ValidationError(
                {"role": ["value must be one of: " + ", ".join(Role.names)]}
            )

        join_request = self.get_object()

        has_membership = Membership.objects.filter(
            site=join_request.site, user=join_request.user
        ).first()
        if has_membership:
            raise ValidationError("User already has a membership on this site")

        with transaction.atomic():
            Membership.objects.create(
                user=join_request.user, site=join_request.site, role=role
            )
            self.update_join_request_status(
                join_request, JoinRequestStatus.APPROVED, request.user
            )

        subject = f"Welcome to the {join_request.site.title} FirstVoices site!"
        message = (
            f"Thank you for requesting to join the {join_request.site.title} site on FirstVoices.\n"
            "A community administrator has approved your request.\n\n"
            f"You are now approved on the {join_request.site.title} site with the role: {role.label}\n"
            ""
        )

        base_url = get_site_url_from_appjson(join_request.site)
        if base_url:
            message = (
                message
                + f"Visit the {join_request.site.title} site here: {base_url}\n\n"
            )

            if role >= Role.ASSISTANT:
                message = (
                    message
                    + f"You now have access to the FirstVoices dashboard for the {join_request.site.title} site. "
                    f"From the dashboard you can create and edit language content, generate reports and access "
                    f"additional administrative features. You can access the dashboard here: {base_url}dashboard\n\n"
                )
            else:
                # user is a member with no dashboard access
                message = (
                    message
                    + f"You now have access to members-only words, phrases, songs and stories on the "
                    f"{join_request.site.title} site.\n\n"
                )
        else:
            message = message + "\n"

        try:
            send_email_task.apply_async((subject, message, [join_request.user.email]))
        except redis.exceptions.ConnectionError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Could not queue task. Error: {e}")

        serializer = self.get_serializer(join_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update_join_request_status(self, join_request, status, user):
        join_request.status = status
        join_request.last_modified_by = user
        join_request.last_modified = datetime.now()
        join_request.save()
