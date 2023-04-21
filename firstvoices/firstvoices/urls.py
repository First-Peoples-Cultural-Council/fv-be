"""firstvoices URL Configuration"""
from backend.admin import admin
from backend.urls import urlpatterns as backend_urls
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf.urls.static import static

from . import settings

urlpatterns = [
	path(settings.ADMIN_URL, admin.site.urls),
	path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
	path(
		"api/docs/",
		SpectacularSwaggerView.as_view(url_name="api-schema"),
		name="api-docs",
	),
]

urlpatterns += backend_urls

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

