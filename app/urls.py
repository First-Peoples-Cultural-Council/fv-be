from django.urls import path, include
from django.utils.safestring import mark_safe
from rest_framework import routers

from . import views


# Modify the main REST API page title and description
class FirstVoicesAPI(routers.APIRootView):
    def get_view_name(self) -> str:
        return "First Voices API"

    def get_view_description(self, html=False) -> str:
        text = "An API used to access data stored on the First Voices Platform."
        if html:
            return mark_safe(f"<p>{text}</p>")
        else:
            return text


class MyRouter(routers.DefaultRouter):
    APIRootView = FirstVoicesAPI


# Regex to match a UUID
regex_uuid = "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"

# Route the URLS to views
router = MyRouter()
router.register(r'languages', views.LanguageViewSet, basename='Language')
router.register(rf'(?P<language_id>{regex_uuid})/words', views.WordViewSet, basename='Word')
router.register(rf'(?P<language_id>{regex_uuid})/phrases', views.PhraseViewSet, basename='Phrase')

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
