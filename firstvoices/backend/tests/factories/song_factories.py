import factory
from factory.django import DjangoModelFactory

from backend.models import Lyric, Song
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.access import SiteFactory


class SongFactory(RelatedMediaBaseFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Song

    title = factory.Sequence(lambda n: "Song title %03d" % n)
    title_translation = factory.Sequence(lambda n: "Song title translation %03d" % n)


class LyricsFactory(DjangoModelFactory):
    site = factory.SubFactory(SongFactory)

    class Meta:
        model = Lyric

    text = factory.Sequence(lambda n: "Song lyric text %03d" % n)
    translation = factory.Sequence(lambda n: "Song lyric translation %03d" % n)
