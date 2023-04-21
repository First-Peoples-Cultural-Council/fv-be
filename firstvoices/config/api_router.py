from backend.views import SiteViewSet
from backend.views.dictionary_views import PartsOfSpeechViewSet
from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r"parts-of-speech", PartsOfSpeechViewSet, basename="parts-of-speech")
router.register(r"sites", SiteViewSet, basename="site")

app_name = "api"
urlpatterns = router.urls
