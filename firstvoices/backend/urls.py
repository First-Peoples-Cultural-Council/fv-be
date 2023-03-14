from rest_framework.routers import DefaultRouter

from backend.viewsets.User import UserViewSet

ROUTER = DefaultRouter(trailing_slash=False)
ROUTER.register(r'api/1.0/user', UserViewSet, basename=r'user')

urlpatterns = []
urlpatterns += ROUTER.urls
