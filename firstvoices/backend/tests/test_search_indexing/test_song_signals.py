from backend.search.indexing.song_index import SongDocumentManager
from backend.tests import factories
from backend.tests.test_search_indexing.base_tests import BaseSignalTest


class TestSongIndexingSignals(BaseSignalTest):
    manager = SongDocumentManager
    factory = factories.SongFactory
    related_factory = factories.LyricsFactory

    def create_related_instance(self, instance):
        return self.related_factory.create(song=instance)
