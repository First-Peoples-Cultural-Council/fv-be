from rest_framework import viewsets

from .serializers import Site, SiteSerializer, Word, WordSerializer


# Create your views here.
# Provides a language endpoint which will use the "can_view_model" rule to check for permission.
class SiteViewSet(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = SiteSerializer

    def get_queryset(self):
        # languages_uuid_list = [language.id for language in Site.objects.all() if
        #                        rules.test_rule('can_view_model', self.request.user, language)]
        # return Site.objects.filter(id__in=languages_uuid_list)
        return Site.objects.all()


# Provides a word endpoint which will first filter words by the language UUID passed from the url and then use the
# "can_view_model" rule to check for permission.
class WordViewSet(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = WordSerializer

    def get_queryset(self):
        site_id = self.kwargs.get("site_id")

        # words_uuid_list = [word.id for word in Word.objects.filter(language__id=language_id) if
        #                    rules.test_rule('can_view_model', self.request.user, word)]
        # return Word.objects.filter(id__in=words_uuid_list, language__id=language_id)
        return Word.objects.filter(site__id=site_id)
