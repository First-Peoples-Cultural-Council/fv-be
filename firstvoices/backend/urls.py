from django.urls import path
from rest_framework.routers import DefaultRouter

from backend.views.dictionary_views import PartsOfSpeechViewSet
from backend.views.sites_views import SiteViewSet
from backend.views.user import UserViewSet

ROUTER = DefaultRouter(trailing_slash=False)
ROUTER.register(r"user", UserViewSet, basename=r"user")
ROUTER.register(r"sites", SiteViewSet, basename="site")
ROUTER.register(r"parts-of-speech", PartsOfSpeechViewSet, basename="parts-of-speech")

app_name = "api"

urlpatterns = []

urlpatterns += ROUTER.urls
