import pytest

from backend.models.media import Image, ImageFile, Video, VideoFile
from backend.serializers.media_serializers import RelatedVideoLinksSerializer
from backend.tests.test_apis.base.base_media_test import (
    MOCK_EMBED_LINK,
    MOCK_THUMBNAIL_LINK,
)

MOCK_MEDIA_DIMENSIONS = {"width": 100, "height": 100}


@pytest.fixture(autouse=True)
def configure_settings(settings):
    # Celery tasks run synchronously for testing
    settings.CELERY_TASK_ALWAYS_EAGER = True


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
