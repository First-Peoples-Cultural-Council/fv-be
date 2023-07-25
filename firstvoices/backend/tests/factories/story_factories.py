import factory
from factory.django import DjangoModelFactory

from backend.models import Story, StoryPage
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.access import SiteFactory


class StoryFactory(RelatedMediaBaseFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Story

    title = factory.Sequence(lambda n: "Story title %03d" % n)
    title_translation = factory.Sequence(lambda n: "Story title translation %03d" % n)


class PagesFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)
    story = factory.SubFactory(StoryFactory)

    class Meta:
        model = StoryPage

    text = factory.Sequence(lambda n: "Story text %03d" % n)
    translation = factory.Sequence(lambda n: "Story text translation %03d" % n)
    ordering = factory.Sequence(lambda n: n)
