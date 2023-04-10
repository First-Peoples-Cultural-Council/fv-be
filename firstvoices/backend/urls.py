from django.urls import path
from rest_framework.routers import DefaultRouter

from backend.views.user import UserViewSet
from backend.views.sites import SiteViewSet
from backend.views.health import HealthCheckView


ROUTER = DefaultRouter(trailing_slash=False)
ROUTER.register(r'api/1.0/user', UserViewSet, basename=r'user')
ROUTER.register(r'api/1.0/site', SiteViewSet)

urlpatterns = [
	path(r'health', HealthCheckView.as_view())
]

urlpatterns += ROUTER.urls
