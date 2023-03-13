from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rules.contrib.rest_framework import AutoPermissionViewSetMixin

from .serializers import (
    Category,
    CategorySerializer,
    Site,
    SiteSerializer,
    Word,
    WordSerializer,
)


# Create your views here.
# Provides a language endpoint which will use the "can_view_model" rule to check for permission.
class SiteViewSet(AutoPermissionViewSetMixin, ModelViewSet):
    http_method_names = ["get"]
    serializer_class = SiteSerializer
    queryset = Site.objects.all()


# Provides a word endpoint which will first filter words by the language UUID passed from the url and then use the
# "can_view_model" rule to check for permission.
class WordViewSet(AutoPermissionViewSetMixin, ModelViewSet):
    serializer_class = WordSerializer

    def list(self, request, **kwargs):
        words_uuid_list = [
            word.id
            for word in self.get_queryset()
            if self.request.user.has_perm("app.view_word", word)
        ]
        queryset = Word.objects.filter(id__in=words_uuid_list)
        serializer = WordSerializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        site_id = self.kwargs.get("site_id")
        return Word.objects.filter(site__id=site_id)


class CategoryViewSet(AutoPermissionViewSetMixin, ModelViewSet):
    serializer_class = CategorySerializer

    def list(self, request, **kwargs):
        uuid_list = [
            category.id
            for category in self.get_queryset()
            if self.request.user.has_perm("app.view_category", category)
        ]
        queryset = Category.objects.filter(id__in=uuid_list)
        serializer = CategorySerializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        site_id = self.kwargs.get("site_id")
        return Category.objects.filter(site__id=site_id)
