from rest_framework_nested.routers import NestedSimpleRouter

from backend.router import CustomRouter
from backend.views.audio_views import AudioViewSet
from backend.views.category_views import CategoryViewSet
from backend.views.character_views import CharactersViewSet, IgnoredCharactersViewSet
from backend.views.contact_us_views import ContactUsView
from backend.views.custom_order_recalculate_views import (
    CustomOrderRecalculatePreviewView,
    CustomOrderRecalculateView,
)
from backend.views.data_views import SitesDataViewSet
from backend.views.dictionary_views import DictionaryViewSet
from backend.views.image_views import ImageViewSet
from backend.views.immersion_label_views import ImmersionLabelViewSet
from backend.views.join_request_views import JoinRequestViewSet
from backend.views.page_views import SitePageViewSet
from backend.views.parts_of_speech_views import PartsOfSpeechViewSet
from backend.views.person_views import PersonViewSet
from backend.views.search.base_search_views import BaseSearchViewSet
from backend.views.search.site_search_views import SiteSearchViewsSet
from backend.views.sites_views import MySitesViewSet, SiteViewSet
from backend.views.song_views import SongViewSet
from backend.views.stats_views import StatsViewSet
from backend.views.story_views import StoryViewSet
from backend.views.storypage_views import StoryPageViewSet
from backend.views.video_views import VideoViewSet
from backend.views.widget_views import SiteWidgetViewSet
from backend.views.word_of_the_day_views import WordOfTheDayView

# app-level APIs

ROUTER = CustomRouter()
ROUTER.register(r"my-sites", MySitesViewSet, basename="my-sites")
ROUTER.register(r"parts-of-speech", PartsOfSpeechViewSet, basename="partofspeech")
ROUTER.register(r"search", BaseSearchViewSet, basename="search")

ROUTER.register(r"sites", SiteViewSet, basename="site")

# site-level APIs
sites_router = NestedSimpleRouter(ROUTER, r"sites", lookup="site")
sites_router.register(r"audio", AudioViewSet, basename="audio")
sites_router.register(r"categories", CategoryViewSet, basename="category")
sites_router.register(r"characters", CharactersViewSet, basename="character")
sites_router.register(r"contact-us", ContactUsView, basename="contact-us")
sites_router.register(r"data", SitesDataViewSet, basename="data")
sites_router.register(r"dictionary", DictionaryViewSet, basename="dictionaryentry")
sites_router.register(
    r"dictionary-cleanup/preview",
    CustomOrderRecalculatePreviewView,
    basename="dictionary-cleanup-preview",
)
sites_router.register(
    r"dictionary-cleanup",
    CustomOrderRecalculateView,
    basename="dictionary-cleanup",
)
sites_router.register(
    r"ignored-characters", IgnoredCharactersViewSet, basename="ignoredcharacter"
)
sites_router.register(r"images", ImageViewSet, basename="image")
sites_router.register(
    r"immersion-labels", ImmersionLabelViewSet, basename="immersionlabel"
)
sites_router.register(r"join-requests", JoinRequestViewSet, basename="joinrequest")
sites_router.register(r"people", PersonViewSet, basename="person")
sites_router.register(r"search", SiteSearchViewsSet, basename="site-search")
sites_router.register(r"word-of-the-day", WordOfTheDayView, basename="word-of-the-day")
sites_router.register(r"pages", SitePageViewSet, basename="sitepage")
sites_router.register(r"songs", SongViewSet, basename="song")
sites_router.register(r"videos", VideoViewSet, basename="video")
sites_router.register(r"widgets", SiteWidgetViewSet, basename="sitewidget")
sites_router.register(r"stats", StatsViewSet, basename="stats")

# stories and pages
sites_router.register(r"stories", StoryViewSet, basename="story")
stories_router = NestedSimpleRouter(sites_router, r"stories", lookup="story")
stories_router.register(r"pages", StoryPageViewSet, basename="storypage")

app_name = "api"

urlpatterns = []

urlpatterns += ROUTER.urls
urlpatterns += sites_router.urls + stories_router.urls
