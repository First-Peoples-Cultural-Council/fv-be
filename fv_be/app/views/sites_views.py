from rest_framework.viewsets import ModelViewSet

from fv_be.app.serializers import Site, SiteSerializer
from fv_be.app.views.base_views import FVPermissionViewSetMixin


class SiteViewSet(FVPermissionViewSetMixin, ModelViewSet):
    # todo: real api implementation
    http_method_names = ["get"]
    serializer_class = SiteSerializer
    queryset = Site.objects.all()
