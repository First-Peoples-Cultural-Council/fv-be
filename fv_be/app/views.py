from rest_framework.mixins import ListModelMixin
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
class WordViewSet(AutoPermissionViewSetMixin, ModelViewSet, ListModelMixin):
    serializer_class = WordSerializer

    def get_queryset(self):
        site_id = self.kwargs.get("site_id")
        return Word.objects.filter(site__id=site_id)
        # site_id = self.kwargs.get("site_id")
        # words_uuid_list = [word.id for word in Word.objects.filter(site__id=site_id) if
        #                    rules.test_rule('app.view_word', self.request.user, word)]
        # return Word.objects.filter(id__in=words_uuid_list)


class CategoryViewSet(AutoPermissionViewSetMixin, ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        site_id = self.kwargs.get("site_id")
        return Category.objects.filter(site__id=site_id)
