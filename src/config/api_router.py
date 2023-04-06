from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from firstvoices.backend.views.dictionary_views import PartsOfSpeechViewSet
from firstvoices.backend.views.sites_views import SiteViewSet
from firstvoices.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r"sites", SiteViewSet, basename="Sites")
router.register(r"parts-of-speech", PartsOfSpeechViewSet, basename="parts-of-speech")
router.register("users", UserViewSet)

app_name = "api"
urlpatterns = router.urls
