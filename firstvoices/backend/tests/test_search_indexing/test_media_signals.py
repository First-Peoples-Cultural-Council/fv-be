from backend.search.indexing import (
    AudioDocumentManager,
    DocumentDocumentManager,
    ImageDocumentManager,
    VideoDocumentManager,
)
from backend.tests import factories
from backend.tests.test_search_indexing.base_indexing_tests import BaseSignalTest


class TestAudioIndexingSignals(BaseSignalTest):
    manager = AudioDocumentManager
    factory = factories.AudioFactory


class TestDocumentIndexingSignals(BaseSignalTest):
    manager = DocumentDocumentManager
    factory = factories.DocumentFactory


class TestImageIndexingSignals(BaseSignalTest):
    manager = ImageDocumentManager
    factory = factories.ImageFactory


class TestVideoIndexingSignals(BaseSignalTest):
    manager = VideoDocumentManager
    factory = factories.VideoFactory
