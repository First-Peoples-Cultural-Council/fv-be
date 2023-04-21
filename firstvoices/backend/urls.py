from django.urls import path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from backend.views.user import UserViewSet
from backend.views.sites import SiteViewSet
from backend.views.health import HealthCheckView


ROUTER = DefaultRouter(trailing_slash=False)
ROUTER.register(r'api/1.0/user', UserViewSet, basename=r'user')
ROUTER.register(r'api/1.0/sites', SiteViewSet)

urlpatterns = [
	path(r'health', HealthCheckView.as_view()),
	# path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
	# path(
	# 	"api/docs/",
	# 	SpectacularSwaggerView.as_view(url_name="api-schema"),
	# 	name="api-docs",
	# ),
]

urlpatterns += ROUTER.urls
