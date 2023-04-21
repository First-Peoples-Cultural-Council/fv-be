from backend.serializers.dictionary_serializers import (
    PartOfSpeech,
    PartsOfSpeechSerializer,
)
from backend.views.base_views import FVPermissionViewSetMixin
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet


@extend_schema_view(
    list=extend_schema(
        description="A list of different parts-of-speech available that different words/phrases can be assigned to.",
        responses={200: PartsOfSpeechSerializer},
    ),
    retrieve=extend_schema(
        description="Details about a specific part of speech.",
        responses={200: PartsOfSpeechSerializer},
    ),
)
class PartsOfSpeechViewSet(FVPermissionViewSetMixin, ModelViewSet):
    http_method_names = ["get"]
    serializer_class = PartsOfSpeechSerializer
    queryset = PartOfSpeech.objects.prefetch_related("children").all()

    @staticmethod
    def get_list_queryset():
        return PartOfSpeech.objects.prefetch_related("children").exclude(
            parent__isnull=False
        )
