import os
import sys

import factory

from django.conf import settings
from embed_video.fields import EmbedVideoField
from django.core.files.uploadedfile import InMemoryUploadedFile

from factory.django import DjangoModelFactory

from backend.models.media import (
    Audio,
    AudioSpeaker,
    EmbeddedVideo,
    File,
    Image,
    ImageFile,
    Person,
    Video,
    VideoFile,
)
from backend.tests.factories.access import SiteFactory


class FileFactory(DjangoModelFactory):
    class Meta:
        model = File

    site = factory.SubFactory(SiteFactory)
    content = factory.django.FileField()


class ImageFileFactory(DjangoModelFactory):
    class Meta:
        model = ImageFile

    site = factory.SubFactory(SiteFactory)
    content = factory.django.ImageField()


class ImageFactory(DjangoModelFactory):
    class Meta:
        model = Image

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Image-%03d" % n)
    original = factory.SubFactory(ImageFileFactory)
    thumbnail = factory.SubFactory(ImageFileFactory)
    small = factory.SubFactory(ImageFileFactory)
    medium = factory.SubFactory(ImageFileFactory)


def get_video_content(size="thumbnail"):
    path = (
        os.path.dirname(os.path.realpath(__file__))
        + f"/resources/video_example_{size}.mp4"
    )
    image_file = open(path, "rb")
    content = InMemoryUploadedFile(
        image_file,
        "FileField",
        "TestVideo.mp4",
        "video/mp4",
        sys.getsizeof(image_file),
        None,
    )
    return content


class VideoFileFactory(DjangoModelFactory):
    class Meta:
        model = VideoFile

    site = factory.SubFactory(SiteFactory)
    content = factory.django.FileField(from_func=get_video_content)


class VideoFactory(DjangoModelFactory):
    class Meta:
        model = Video

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Video-%03d" % n)
    original = factory.SubFactory(VideoFileFactory)


class EmbeddedVideoFactory(DjangoModelFactory):
    class Meta:
        model = EmbeddedVideo

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Embedded-Video-%03d" % n)
    content = EmbedVideoField("https://www.youtube.com/")


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
    original = factory.SubFactory(FileFactory)


class AudioSpeakerFactory(DjangoModelFactory):
    class Meta:
        model = AudioSpeaker

    site = factory.SubFactory(SiteFactory)
    audio = factory.SubFactory(AudioFactory)
    speaker = factory.SubFactory(PersonFactory)


class RelatedMediaBaseFactory(DjangoModelFactory):
    class Meta:
        abstract = True

    @factory.post_generation
    def related_audio(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        if extracted:
            # A list of image were passed in, use them
            for e in extracted:
                self.related_audio.add(e)

    @factory.post_generation
    def related_images(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of image were passed in, use them
            for e in extracted:
                self.related_images.add(e)

    @factory.post_generation
    def related_videos(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of image were passed in, use them
            for e in extracted:
                self.related_videos.add(e)
