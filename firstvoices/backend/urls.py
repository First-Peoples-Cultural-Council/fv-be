from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from backend.views.health import HealthCheckView
from backend.views.sites_views import SiteViewSet
from backend.views.user import UserViewSet

ROUTER = DefaultRouter(trailing_slash=False)
ROUTER.register(r"api/1.0/user", UserViewSet, basename=r"user")
ROUTER.register(r"api/1.0/sites", SiteViewSet)

urlpatterns = [
    path(r"health", HealthCheckView.as_view()),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]

urlpatterns += ROUTER.urls
