from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet

from backend.models import Story, StoryPage
from backend.views.base_views import FVPermissionViewSetMixin, SiteContentViewSetMixin

from ..serializers.story_serializers import StoryPageDetailSerializer
from . import doc_strings
from .api_doc_variables import id_parameter, site_slug_parameter


@extend_schema_view(
    list=extend_schema(
        description=_("A list of story pages associated with the specified site."),
        parameters=[site_slug_parameter],
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_list,
                response=StoryPageDetailSerializer,
            ),
            403: OpenApiResponse(description=doc_strings.error_403_site_access_denied),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
    ),
    retrieve=extend_schema(
        description=_("Details about a specific story page."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_detail,
                response=StoryPageDetailSerializer,
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
        description=_("Add a story page."),
        responses={
            201: OpenApiResponse(
                description=doc_strings.success_201, response=StoryPageDetailSerializer
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter],
    ),
    update=extend_schema(
        description=_("Edit a story page."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=StoryPageDetailSerializer,
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
        description=_("Edit a story page. Any omitted fields will be unchanged."),
        responses={
            200: OpenApiResponse(
                description=doc_strings.success_200_edit,
                response=StoryPageDetailSerializer,
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
        description=_("Delete a story page."),
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
class StoryPageViewSet(SiteContentViewSetMixin, FVPermissionViewSetMixin, ModelViewSet):
    def get_detail_queryset(self):
        site = self.get_validated_site()
        story = self.get_validated_story(site)
        return StoryPage.objects.filter(site=site, story=story).all()

    def get_list_queryset(self):
        site = self.get_validated_site()
        story = self.get_validated_story(site)
        return StoryPage.objects.filter(site=site, story=story).order_by("id").all()

    def get_serializer_class(self):
        return StoryPageDetailSerializer

    def get_story_id(self):
        return self.kwargs["story_pk"]

    def get_serializer_context(self):
        """
        Add the site to the extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        context["story"] = self.get_validated_story(context["site"])
        return context

    def get_validated_story(self, site):
        story_id = self.get_story_id()
        try:
            story = Story.objects.filter(pk=story_id, site=site)
        except ValidationError:
            # story id is not a valid uuid
            raise Http404

        if len(story) == 0:
            raise Http404

        # Check if story is visible
        perm = Story.get_perm("view")
        story = story.first()
        if not self.request.user.has_perm(perm, story):
            raise PermissionDenied
        else:
            return story
