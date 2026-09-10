import os

import pytest
from celery import current_app as celery_app

from backend.models.media import Image, ImageFile, Video, VideoFile
from backend.serializers.media_serializers import RelatedVideoLinksSerializer
from backend.tests.test_apis.base.base_media_test import (
    MOCK_EMBED_LINK,
    MOCK_THUMBNAIL_LINK,
)

MOCK_MEDIA_DIMENSIONS = {"width": 100, "height": 100}

os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "True")
os.environ.setdefault("CELERY_TASK_EAGER_PROPAGATES", "True")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

try:
    # If Celery was already imported, patching its runtime config
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
except Exception:
    # Ignore if celery is not available
    pass


@pytest.fixture(autouse=True)
def image_thumbnail_generation_does_nothing(request, mocker):
    if "disable_thumbnail_mocks" not in request.keywords:
        mocker.patch.object(Image, "_request_thumbnail_generation", return_value=None)
    yield


@pytest.fixture(autouse=True)
def video_thumbnail_generation_does_nothing(request, mocker):
    if "disable_thumbnail_mocks" not in request.keywords:
        mocker.patch.object(Video, "_request_thumbnail_generation", return_value=None)
    yield


@pytest.fixture(autouse=True)
def mock_get_video_dimensions(request, mocker):
    if "disable_thumbnail_mocks" not in request.keywords:
        mocker.patch.object(
            VideoFile, "get_video_info", return_value=MOCK_MEDIA_DIMENSIONS
        )
    yield


@pytest.fixture(autouse=True)
def mock_get_image_dimensions(request, mocker):
    if "disable_thumbnail_mocks" not in request.keywords:
        mocker.patch.object(
            ImageFile, "get_image_dimensions", return_value=MOCK_MEDIA_DIMENSIONS
        )
    yield


@pytest.fixture(autouse=True)
def related_video_links_embed_and_thumbnail_does_nothing(request, mocker):
    if "disable_related_video_link_mocks" not in request.keywords:
        mocker.patch.object(
            RelatedVideoLinksSerializer,
            "get_embed_link",
            return_value=MOCK_EMBED_LINK,
        )
        mocker.patch.object(
            RelatedVideoLinksSerializer,
            "get_thumbnail",
            return_value=MOCK_THUMBNAIL_LINK,
        )
    yield
