from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from firstvoices.backend.views.sites_views import SiteFilteredList

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r"sites", SiteFilteredList, basename="site")
# router.register("users", UserViewSet)

app_name = "api"
urlpatterns = router.urls
