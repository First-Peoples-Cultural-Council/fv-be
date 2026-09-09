from django.http import Http404
from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, viewsets

from backend.models import Audio, Document, Image, Song, Story, Video
from backend.models.dictionary import DictionaryEntry
from backend.serializers.lookup_serializers import (
    AudioLookupSerializer,
    DictionaryEntryLookupSerializer,
    DocumentLookupSerializer,
    ImageLookupSerializer,
    SongLookupSerializer,
    StoryLookupSerializer,
    VideoLookupSerializer,
)
from backend.utils.uuid_utils import is_valid_uuid
from backend.views.base_views import FVPermissionViewSetMixin

from . import doc_strings
from .api_doc_variables import id_parameter


@extend_schema_view(
    retrieve=extend_schema(
        description=_(
            "Look up an object by its UUID, across all supported content type."
            "Returns identifying information and a link to the object's detail view."
        ),
        responses={
            200: inline_serializer(
                name="LookupResult",
                fields={
                    "id": serializers.UUIDField(),
                    "type": serializers.CharField(),
                    "title": serializers.CharField(),
                    "url": serializers.URLField(),
                    "site": serializers.DictField(),
                    "created": serializers.DateTimeField(),
                    "createdBy": serializers.CharField(),
                    "lastModified": serializers.DateTimeField(),
                    "lastModifiedBy": serializers.CharField(),
                    "systemLastModified": serializers.DateTimeField(),
                    "systemLastModifiedBy": serializers.CharField(),
                },
            ),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404),
        },
        parameters=[id_parameter],
    ),
)
class LookupViewSet(
    FVPermissionViewSetMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Look up a single object by UUID across all supported content types.

    UUIDs are globally unique, so the caller does not need to know the site or the
    content type in advance. The model is resolved from the id, then the standard
    permission rules for that model are applied.
    """

    http_method_names = ["get"]

    serializers = {
        Audio: AudioLookupSerializer,
        Document: DocumentLookupSerializer,
        Image: ImageLookupSerializer,
        Video: VideoLookupSerializer,
        DictionaryEntry: DictionaryEntryLookupSerializer,
        Song: SongLookupSerializer,
        Story: StoryLookupSerializer,
    }

    _cached_model = None

    def get_model(self):
        """
        Resolves which model the requested id belongs to. Cached because the permission
        check and the object lookup both need it within a single request.
        """
        if self._cached_model is not None:
            return self._cached_model

        lookup_id = self.kwargs["pk"]

        # an unparseable id is treated the same as an id that doesn't exist.
        if not is_valid_uuid(lookup_id):
            raise Http404

        for model in self.serializers:
            if model.objects.filter(id=lookup_id).exists():
                self._cached_model = model
                return model

        raise Http404

    def get_detail_queryset(self):
        return self.get_model().objects.select_related(
            "site", "created_by", "last_modified_by", "system_last_modified_by"
        )

    def get_serializer_class(self):
        return self.serializers[self.get_model()]
