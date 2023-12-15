from unittest.mock import patch

import pytest

from backend.models.media import Image, ImageFile, Video, VideoFile
from backend.serializers.media_serializers import RelatedVideoLinksSerializer

MOCK_MEDIA_DIMENSIONS = {"width": 100, "height": 100}


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


@pytest.fixture(autouse=True, scope="session")
def mock_search_indexing():
    with (
        patch(
            "backend.search.signals.dictionary_entry_signals.update_dictionary_entry_index"
        ) as mocked_update_dictionary_entry_index,
        patch(
            "backend.search.signals.dictionary_entry_signals.delete_from_index"
        ) as mocked_delete_dictionary_entry_index,
        patch(
            "backend.search.signals.dictionary_entry_signals.update_translation"
        ) as mocked_update_translation,
        patch(
            "backend.search.signals.dictionary_entry_signals.update_notes"
        ) as mocked_update_notes,
        patch(
            "backend.search.signals.dictionary_entry_signals.update_acknowledgements"
        ) as mocked_update_acknowledgements,
        patch(
            "backend.search.signals.dictionary_entry_signals.update_categories"
        ) as mocked_update_categories,
        patch(
            "backend.search.signals.dictionary_entry_signals.update_categories_m2m"
        ) as mocked_update_categories_m2m,
        patch(
            "backend.search.signals.song_signals.update_song_index"
        ) as mocked_update_song_index,
        patch(
            "backend.search.signals.song_signals.delete_from_index"
        ) as mocked_delete_song_index,
        patch(
            "backend.search.signals.song_signals.update_lyrics"
        ) as mocked_update_lyrics,
        patch(
            "backend.search.signals.story_signals.update_story_index"
        ) as mocked_update_story_index,
        patch(
            "backend.search.signals.story_signals.delete_from_index"
        ) as mocked_delete_story_index,
        patch(
            "backend.search.signals.story_signals.update_pages"
        ) as mocked_request_update_pages,
        patch(
            "backend.search.signals.media_signals.update_media_index"
        ) as mocked_update_media_index,
        patch(
            "backend.search.signals.media_signals.delete_from_index"
        ) as mocked_delete_media_index,
        patch(
            "backend.search.signals.site_signals.update_document_visibility"
        ) as mocked_update_document_visibility,
        patch(
            "backend.search.signals.site_signals.delete_related_docs"
        ) as mocked_delete_related_docs,
    ):
        mocked_update_dictionary_entry_index.return_value = None
        mocked_delete_dictionary_entry_index.return_value = None
        mocked_update_translation.return_value = None
        mocked_update_notes.return_value = None
        mocked_update_acknowledgements.return_value = None
        mocked_update_categories.return_value = None
        mocked_update_categories_m2m.return_value = None
        mocked_update_song_index.return_value = None
        mocked_delete_song_index.return_value = None
        mocked_update_lyrics.return_value = None
        mocked_update_story_index.return_value = None
        mocked_delete_story_index.return_value = None
        mocked_request_update_pages.return_value = None
        mocked_update_document_visibility.return_value = None
        mocked_delete_related_docs.return_value = None
        mocked_update_media_index.return_value = None
        mocked_delete_media_index.return_value = None
        yield


@pytest.fixture(autouse=True)
def related_video_links_embed_and_thumbnail_does_nothing(request, mocker):
    if "disable_related_video_link_mocks" not in request.keywords:
        mocker.patch.object(
            RelatedVideoLinksSerializer,
            "get_embed_link",
            return_value="https://mock_embed_link.com/",
        )
        mocker.patch.object(
            RelatedVideoLinksSerializer,
            "get_thumbnail",
            return_value="https://mock_thumbnail_link.com/",
        )
    yield
