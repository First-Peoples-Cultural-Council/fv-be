from rest_framework.viewsets import ModelViewSet

from backend.models import Site
from backend.serializers.site import SiteSerializer
from backend.views.base import FVPermissionViewSetMixin


class SiteViewSet(FVPermissionViewSetMixin, ModelViewSet):
    # stub
    http_method_names = ["get"]
    serializer_class = SiteSerializer
    queryset = Site.objects.all()
