from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from firstvoices.backend.views.character_views import CharactersViewSet
from firstvoices.backend.views.dictionary_views import PartsOfSpeechViewSet
from firstvoices.backend.views.sites_views import SiteViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r"characters", CharactersViewSet, basename="characters")
router.register(r"parts-of-speech", PartsOfSpeechViewSet, basename="parts-of-speech")
router.register(r"sites", SiteViewSet, basename="site")

app_name = "api"
urlpatterns = router.urls
