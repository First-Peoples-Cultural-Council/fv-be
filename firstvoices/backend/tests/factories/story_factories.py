import factory

from backend.models import Story, StoryPage
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.access import SiteFactory, UserFactory


class StoryFactory(RelatedMediaBaseFactory):
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Story

    title = factory.Sequence(lambda n: "Story title %03d" % n)
    title_translation = factory.Sequence(lambda n: "Story title translation %03d" % n)
    author = factory.Sequence(lambda n: "Author for story %03d" % n)


class StoryPageFactory(RelatedMediaBaseFactory):
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)
    story = factory.SubFactory(StoryFactory)

    class Meta:
        model = StoryPage

    text = factory.Sequence(lambda n: "Story text %03d" % n)
    translation = factory.Sequence(lambda n: "Story text translation %03d" % n)
    ordering = factory.Sequence(lambda n: n)
