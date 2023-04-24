from rest_framework.routers import DefaultRouter

from backend.views.character_views import CharactersViewSet
from backend.views.dictionary_views import PartsOfSpeechViewSet
from backend.views.sites_views import SiteViewSet
from backend.views.user import UserViewSet

ROUTER = DefaultRouter(trailing_slash=False)
ROUTER.register(r"user", UserViewSet, basename=r"user")
ROUTER.register(r"sites", SiteViewSet, basename="site")
ROUTER.register(r"parts-of-speech", PartsOfSpeechViewSet, basename="parts-of-speech")
ROUTER.register(r"characters", CharactersViewSet, basename="characters")

app_name = "api"

urlpatterns = []

urlpatterns += ROUTER.urls
