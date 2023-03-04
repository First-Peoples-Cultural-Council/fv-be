from .serializers import *
from rest_framework import viewsets
from rules.contrib.rest_framework import AutoPermissionViewSetMixin
from .predicates import *


# Provides a language endpoint which will use the "can_view_model" rule to check for permission.
class LanguageViewSet(AutoPermissionViewSetMixin, viewsets.ModelViewSet):
    http_method_names = ['get']
    serializer_class = LanguageSerializer

    def get_queryset(self):
        languages_uuid_list = [language.id for language in Language.objects.all() if
                               rules.test_rule('can_view_model', self.request.user, language)]
        return Language.objects.filter(id__in=languages_uuid_list)


# Provides a word endpoint which will first filter words by the language UUID passed from the url and then use the
# "can_view_model" rule to check for permission.
class WordViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    serializer_class = WordSerializer

    def get_queryset(self):
        language_id = self.kwargs.get('language_id')

        words_uuid_list = [word.id for word in Word.objects.filter(language__id=language_id) if
                           rules.test_rule('can_view_model', self.request.user, word)]
        return Word.objects.filter(id__in=words_uuid_list, language__id=language_id)


# Provides a phrase endpoint which will first filter phrases by the language UUID passed from the url and then use the
# "can_view_model" rule to check for permission.
class PhraseViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    serializer_class = PhraseSerializer

    def get_queryset(self):
        language_id = self.kwargs.get('language_id')
        phrases_uuid_list = [phrase.id for phrase in Phrase.objects.all(language_id=language_id) if
                             rules.test_rule('can_view_model', self.request.user, phrase)]
        return Phrase.objects.filter(id__in=phrases_uuid_list)
