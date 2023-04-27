from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from backend.views.dictionary_views import DictionaryViewSet
from backend.views.parts_of_speech_views import PartsOfSpeechViewSet
from backend.views.sites_views import SiteViewSet
from backend.views.user import UserViewSet

# app-level APIs
ROUTER = DefaultRouter(trailing_slash=True)
ROUTER.register(r"user", UserViewSet, basename=r"user")
ROUTER.register(r"parts-of-speech", PartsOfSpeechViewSet, basename="parts-of-speech")
ROUTER.register(r"sites", SiteViewSet, basename="site")

# site-level APIs
sites_router = NestedSimpleRouter(ROUTER, r"sites", lookup="site")
sites_router.register(r"dictionary", DictionaryViewSet, basename="dictionary")

app_name = "api"

urlpatterns = []

urlpatterns += ROUTER.urls
urlpatterns += sites_router.urls
