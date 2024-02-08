from backend.search.indexing.story_index import StoryDocumentManager
from backend.tests import factories
from backend.tests.test_search_indexing.base_tests import BaseSignalTest


class TestStoryIndexingSignals(BaseSignalTest):
    manager = StoryDocumentManager
    factory = factories.StoryFactory
    related_factory = factories.StoryPageFactory

    def create_related_instance(self, instance):
        return self.related_factory.create(story=instance)
