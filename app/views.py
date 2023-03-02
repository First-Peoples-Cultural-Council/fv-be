from .serializers import *
from rest_framework import viewsets
from guardian.shortcuts import get_objects_for_user, get_perms


# Provides a language endpoint using the guardian get_objects_for_user which will only return models that the
# user has the "view_language" permission on
class LanguageViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    serializer_class = LanguageSerializer

    def get_queryset(self):
        if Language.objects.values() is None:
            return {}
        else:
            return get_objects_for_user(self.request.user, 'view_language', Language.objects.values())


# Provides a word endpoint which first checks for permission to view the language passed as a UUID from the url and
# then checks if the user has permission to view the word. It returns all words for the language.
class WordViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    serializer_class = WordSerializer

    def get_queryset(self):
        language = Language.objects.get(id=self.kwargs.get('language_id'))
        if self.request.user.has_perm('view_language', language):
            return get_objects_for_user(self.request.user, 'view_word', language.word_set.all())
        else:
            return Word.objects.none()


# Provides a phrase endpoint which first checks for permission to view the language passed as a UUID from the url and
# then checks if the user has permission to view the phrase. It returns all phrases for the language.
class PhraseViewSet(viewsets.ModelViewSet):
    http_method_names = ['get']
    serializer_class = PhraseSerializer

    def get_queryset(self):
        language = Language.objects.get(id=self.kwargs.get('language_id'))
        if self.request.user.has_perm('view_language', language):
            return get_objects_for_user(self.request.user, 'view_phrase', language.phrase_set.all())
        else:
            return Phrase.objects.none()
