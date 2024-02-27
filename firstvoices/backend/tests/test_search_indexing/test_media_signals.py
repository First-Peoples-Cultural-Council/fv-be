from backend.search.indexing import (
    AudioDocumentManager,
    ImageDocumentManager,
    VideoDocumentManager,
)
from backend.tests import factories
from backend.tests.test_search_indexing.base_indexing_tests import BaseSignalTest


class TestAudioIndexingSignals(BaseSignalTest):
    manager = AudioDocumentManager
    factory = factories.AudioFactory


class TestImageIndexingSignals(BaseSignalTest):
    manager = ImageDocumentManager
    factory = factories.ImageFactory


class TestVideoIndexingSignals(BaseSignalTest):
    manager = VideoDocumentManager
    factory = factories.VideoFactory
