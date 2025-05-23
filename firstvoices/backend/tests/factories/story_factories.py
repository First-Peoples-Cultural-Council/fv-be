import factory

from backend.models import Story, StoryPage
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.base_factories import BaseSiteContentFactory


class StoryFactory(BaseSiteContentFactory, RelatedMediaBaseFactory):
    class Meta:
        model = Story

    title = factory.Sequence(lambda n: "Story title %03d" % n)
    title_translation = factory.Sequence(lambda n: "Story title translation %03d" % n)
    author = factory.Sequence(lambda n: "Author for story %03d" % n)


class StoryPageFactory(BaseSiteContentFactory, RelatedMediaBaseFactory):
    class Meta:
        model = StoryPage

    story = factory.SubFactory(StoryFactory)
    text = factory.Sequence(lambda n: "Story text %03d" % n)
    translation = factory.Sequence(lambda n: "Story text translation %03d" % n)
    ordering = factory.Sequence(lambda n: n)
