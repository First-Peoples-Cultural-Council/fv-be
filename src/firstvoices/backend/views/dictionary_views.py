from rest_framework.viewsets import ModelViewSet

from firstvoices.backend.serializers.dictionary_serializers import (
    PartOfSpeech,
    PartsOfSpeechSerializer,
)
from firstvoices.backend.views.base_views import FVPermissionViewSetMixin


class PartsOfSpeechViewSet(FVPermissionViewSetMixin, ModelViewSet):
    http_method_names = ["get"]
    serializer_class = PartsOfSpeechSerializer
    queryset = PartOfSpeech.objects.all()
