from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from backend.views.category_views import CategoryViewSet
from backend.views.character_views import CharactersViewSet, IgnoredCharactersViewSet
from backend.views.custom_order_recalculate_views import (
    CustomOrderRecalculatePreviewView,
    CustomOrderRecalculateView,
)
from backend.views.data_views import SitesDataViewSet
from backend.views.dictionary_views import DictionaryViewSet
from backend.views.parts_of_speech_views import PartsOfSpeechViewSet
from backend.views.search.search_views import SearchViewSet
from backend.views.sites_views import MySitesViewSet, SiteViewSet
from backend.views.user import UserViewSet
from backend.views.word_of_the_day_views import WordOfTheDayView

# app-level APIs
ROUTER = DefaultRouter(trailing_slash=True)
ROUTER.register(r"my-sites", MySitesViewSet, basename="my-sites")
ROUTER.register(r"parts-of-speech", PartsOfSpeechViewSet, basename="partofspeech")
ROUTER.register(r"search", SearchViewSet, basename="search")
ROUTER.register(r"user", UserViewSet, basename=r"user")
ROUTER.register(r"sites", SiteViewSet, basename="site")

# site-level APIs
sites_router = NestedSimpleRouter(ROUTER, r"sites", lookup="site")
sites_router.register(r"categories", CategoryViewSet, basename="category")
sites_router.register(r"characters", CharactersViewSet, basename="character")
sites_router.register(r"dictionary", DictionaryViewSet, basename="dictionaryentry")
sites_router.register(r"data", SitesDataViewSet, basename="data")
sites_router.register(
    r"dictionary-cleanup",
    CustomOrderRecalculatePreviewView,
    basename="dictionary-cleanup",
)
sites_router.register(
    r"dictionary-cleanup/preview",
    CustomOrderRecalculatePreviewView,
    basename="dictionary-cleanup/preview",
)
sites_router.register(
    r"ignored-characters", IgnoredCharactersViewSet, basename="ignoredcharacter"
)
sites_router.register(r"word-of-the-day", WordOfTheDayView, basename="word-of-the-day")

app_name = "api"

urlpatterns = []

urlpatterns += ROUTER.urls
urlpatterns += sites_router.urls
