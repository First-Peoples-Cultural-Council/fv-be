from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from firstvoices.backend.serializers.dictionary_serializers import (
    PartOfSpeech,
    PartsOfSpeechSerializer,
)
from firstvoices.backend.views.base_views import FVPermissionViewSetMixin


@extend_schema_view(
    list=extend_schema(
        description="A list of different parts-of-speech available that different words/phrases can be assigned to.",
        responses={200: PartsOfSpeechSerializer},
    ),
    retrieve=extend_schema(description="Details about a specific parts-of-speech."),
)
class PartsOfSpeechViewSet(FVPermissionViewSetMixin, ModelViewSet):
    http_method_names = ["get"]
    serializer_class = PartsOfSpeechSerializer
    queryset = PartOfSpeech.objects.all()
