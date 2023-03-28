from django.urls import path
from rest_framework.routers import DefaultRouter

from backend.views import HealthCheckView
from backend.viewsets.User import UserViewSet

ROUTER = DefaultRouter(trailing_slash=False)
ROUTER.register(r'api/1.0/user', UserViewSet, basename=r'user')

urlpatterns = [
	path(r'health', HealthCheckView.as_view())
]

urlpatterns += ROUTER.urls
