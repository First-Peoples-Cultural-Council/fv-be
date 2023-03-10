from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from fv_be.app.views import SiteViewSet, WordViewSet
from fv_be.users.api.views import UserViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

# Regex to match a UUID
regex_uuid = "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"

router.register("users", UserViewSet)
router.register(r"sites", SiteViewSet, basename="Sites")
router.register(rf"sites/(?P<site_id>{regex_uuid})/words", WordViewSet, basename="Word")

app_name = "api"
urlpatterns = router.urls
