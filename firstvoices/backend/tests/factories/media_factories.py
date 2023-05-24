import factory
from factory.django import DjangoModelFactory

from backend.models.media import Audio, AudioSpeaker, Image, Person, Video
from backend.tests.factories.access import SiteFactory


class ImageFactory(DjangoModelFactory):
    class Meta:
        model = Image

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Image-%03d" % n)
    content = factory.django.ImageField()


class VideoFactory(DjangoModelFactory):
    class Meta:
        model = Video

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Video-%03d" % n)
    content = factory.django.FileField()


class PersonFactory(DjangoModelFactory):
    class Meta:
        model = Person

    site = factory.SubFactory(SiteFactory)
    name = factory.Sequence(lambda n: "Person %03d" % n)


class AudioFactory(DjangoModelFactory):
    class Meta:
        model = Audio

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Audio-%03d" % n)
    content = factory.django.FileField()


class AudioSpeakerFactory(DjangoModelFactory):
    class Meta:
        model = AudioSpeaker

    site = factory.SubFactory(SiteFactory)
    audio = factory.SubFactory(AudioFactory)
    speaker = factory.SubFactory(PersonFactory)
