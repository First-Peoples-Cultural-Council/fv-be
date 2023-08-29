from unittest.mock import patch

import pytest


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
