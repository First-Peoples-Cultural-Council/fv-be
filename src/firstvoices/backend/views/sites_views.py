from rest_framework.viewsets import ModelViewSet

from firstvoices.backend.serializers import Site, SiteSerializer
from firstvoices.backend.views.base_views import FVPermissionViewSetMixin


class SiteViewSet(AutoPermissionViewSetMixin, ModelViewSet):
    # stub
    http_method_names = ["get"]
    serializer_class = SiteSerializer
    queryset = Site.objects.all()
