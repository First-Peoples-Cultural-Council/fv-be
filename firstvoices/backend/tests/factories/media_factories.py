import mimetypes
import os
import sys

import factory
from django.core.files.uploadedfile import InMemoryUploadedFile
from factory.django import DjangoModelFactory

from backend.models.media import (
    SUPPORTED_FILETYPES,
    Audio,
    AudioSpeaker,
    Document,
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


def get_image_content(size="thumbnail", file_type="image/png"):
    allowed_types = SUPPORTED_FILETYPES["image"]
    if file_type not in allowed_types:
        raise ValueError(
            f"File type {file_type} not supported for images. Supported types are: {allowed_types}"
        )

    file_extension = mimetypes.guess_extension(file_type)
    filename = f"image_example_{size}{file_extension}"
    path = os.path.dirname(os.path.realpath(__file__)) + f"/resources/{filename}"
    file = open(path, "rb")
    content = InMemoryUploadedFile(
        file,
        "ImageField",
        filename,
        file_type,
        sys.getsizeof(file),
        None,
    )
    return content


class ImageFileFactory(DjangoModelFactory):
    class Meta:
        model = ImageFile

    site = factory.SubFactory(SiteFactory)
    content = factory.django.ImageField(from_func=get_image_content)


class ImageFactory(DjangoModelFactory):
    class Meta:
        model = Image

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Image-%03d" % n)
    original = factory.SubFactory(ImageFileFactory)


def get_video_content(size="thumbnail"):
    filename = f"video_example_{size}.mp4"
    path = os.path.dirname(os.path.realpath(__file__)) + f"/resources/{filename}"
    file = open(path, "rb")
    content = InMemoryUploadedFile(
        file,
        "FileField",
        filename,
        "video/mp4",
        sys.getsizeof(file),
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


class DocumentFactory(DjangoModelFactory):
    class Meta:
        model = Document

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Document-%03d" % n)
    original = factory.SubFactory(FileFactory)


class AudioSpeakerFactory(DjangoModelFactory):
    class Meta:
        model = AudioSpeaker

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
            # A list of audios were passed in, use them
            for e in extracted:
                self.related_audio.add(e)

    @factory.post_generation
    def related_documents(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        if extracted:
            # A list of documents were passed in, use them
            for e in extracted:
                self.related_documents.add(e)

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
