from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from fv_be.app.views.sites_views import SiteViewSet
from fv_be.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r"sites", SiteViewSet, basename="Sites")
router.register("users", UserViewSet)

app_name = "api"
urlpatterns = router.urls
