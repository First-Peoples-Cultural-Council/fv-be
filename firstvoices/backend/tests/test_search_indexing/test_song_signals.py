from backend.search.indexing.song_index import SongDocumentManager
from backend.tests import factories
from backend.tests.test_search_indexing.base_indexing_tests import (
    BaseRelatedInstanceSignalTest,
)


class TestSongIndexingSignals(BaseRelatedInstanceSignalTest):
    manager = SongDocumentManager
    factory = factories.SongFactory
    related_factories = [factories.LyricsFactory]

    def create_related_instance(self, related_factory, instance):
        return related_factory.create(song=instance)
