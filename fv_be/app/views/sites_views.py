from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from fv_be.app.serializers import Site, SiteSerializer


class SiteViewSet(AutoPermissionViewSetMixin, ModelViewSet):
    # todo: real api implementation
    http_method_names = ["get"]
    serializer_class = SiteSerializer
    queryset = Site.objects.all()

    def list(self, request, **kwargs):
        sites_uuid_list = [
            site.id
            for site in self.get_queryset()
            if self.request.user.has_perm("app.view_site", site)
        ]
        queryset = Site.objects.filter(id__in=sites_uuid_list)
        serializer = SiteSerializer(queryset, many=True)
        return Response(serializer.data)
