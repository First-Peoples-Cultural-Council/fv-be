from django.urls import path
from rest_framework.routers import DefaultRouter

from backend.views.dictionary_views import PartsOfSpeechViewSet
from backend.views.health import HealthCheckView
from backend.views.sites_views import SiteViewSet
from backend.views.user import UserViewSet

ROUTER = DefaultRouter(trailing_slash=False)
ROUTER.register(r"api/1.0/user", UserViewSet, basename=r"user")
ROUTER.register(r"api/1.0/sites", SiteViewSet, basename="site")
ROUTER.register(
    r"api/1.0/parts-of-speech", PartsOfSpeechViewSet, basename="parts-of-speech"
)

app_name = "api"

urlpatterns = [
    path(r"health", HealthCheckView.as_view()),
]

urlpatterns += ROUTER.urls
