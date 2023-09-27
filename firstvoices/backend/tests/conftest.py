from unittest.mock import patch

import pytest

from backend.models.media import ImageFile, VideoFile

MOCK_MEDIA_DIMENSIONS = {"width": 100, "height": 100}


@pytest.fixture(autouse=True, scope="session")
def image_thumbnail_generation_does_nothing():
    with patch("backend.models.media.Image._request_thumbnail_generation") as mocked:
        mocked.return_value = None
        yield


@pytest.fixture(autouse=True, scope="session")
def video_thumbnail_generation_does_nothing():
    with patch("backend.models.media.Video._request_thumbnail_generation") as mocked:
        mocked.return_value = None
        yield


@pytest.fixture(autouse=True)
def mock_get_video_dimensions(mocker):
    mock_video_dimensions = mocker.patch.object(
        VideoFile, "get_video_info", return_value=MOCK_MEDIA_DIMENSIONS
    )
    yield mock_video_dimensions


@pytest.fixture(autouse=True)
def mock_get_image_dimensions(mocker):
    mock_image_dimensions = mocker.patch.object(
        ImageFile, "get_image_dimensions", return_value=MOCK_MEDIA_DIMENSIONS
    )
    yield mock_image_dimensions
