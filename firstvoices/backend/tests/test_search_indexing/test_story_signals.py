from backend.search.indexing.story_index import StoryDocumentManager
from backend.tests import factories
from backend.tests.test_search_indexing.base_indexing_tests import (
    BaseRelatedInstanceSignalTest,
)


class TestStoryIndexingSignals(BaseRelatedInstanceSignalTest):
    manager = StoryDocumentManager
    factory = factories.StoryFactory
    related_factories = [factories.StoryPageFactory]

    def create_related_instance(self, related_factory, instance):
        return related_factory.create(story=instance)
