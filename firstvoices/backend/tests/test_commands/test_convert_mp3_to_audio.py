import os

import pytest
from django.core.management import call_command

from backend.models.media import Audio, Image, ImageFile, Video, VideoFile
from backend.tests import factories
from backend.tests.utils import get_sample_file


class TestConvertMP3ToAudio:
    SAMPLE_FILETYPE = "audio/mp3"
    SAMPLE_FILENAME = "sample-audio.mp3"
    IMAGE_TITLE = "Image with MP3"
    VIDEO_TITLE = "Video with MP3"

    def create_image_model_with_mp3(self, site, title):
        mp3 = ImageFile.objects.create(
            content=get_sample_file(self.SAMPLE_FILENAME, self.SAMPLE_FILETYPE),
            site=site,
        )
        return factories.ImageFactory.create(original=mp3, site=site, title=title)

    def create_video_model_with_mp3(self, site, title):
        mp3 = VideoFile.objects.create(
            content=get_sample_file(self.SAMPLE_FILENAME, self.SAMPLE_FILETYPE),
            site=site,
        )
        return factories.VideoFactory.create(original=mp3, site=site, title=title)

    @staticmethod
    def confirm_model_data(original_model, audio_model):
        assert original_model.created_by == audio_model.created_by
        assert original_model.created == audio_model.created
        assert original_model.last_modified_by == audio_model.last_modified_by
        assert original_model.last_modified == audio_model.last_modified
        assert original_model.site == audio_model.site
        assert original_model.title == audio_model.title
        assert original_model.description == audio_model.description
        assert original_model.acknowledgement == audio_model.acknowledgement
        assert original_model.exclude_from_games == audio_model.exclude_from_games
        assert original_model.exclude_from_kids == audio_model.exclude_from_kids

    @pytest.mark.django_db
    def test_convert_mp3_models_single_site(self):
        site = factories.SiteFactory.create()
        image = self.create_image_model_with_mp3(site, self.IMAGE_TITLE)
        audio = self.create_video_model_with_mp3(site, self.VIDEO_TITLE)

        assert Image.objects.filter(site=site).count() == 1
        assert Video.objects.filter(site=site).count() == 1

        call_command("convert_mp3_to_audio", site_slug=site.slug)

        assert Image.objects.filter(site=site).count() == 0
        assert Video.objects.filter(site=site).count() == 0
        assert Audio.objects.filter(site=site).count() == 2

        converted_image = Audio.objects.get(title=self.IMAGE_TITLE)
        converted_video = Audio.objects.get(title=self.VIDEO_TITLE)

        self.confirm_model_data(image, converted_image)
        self.confirm_model_data(audio, converted_video)

    @pytest.mark.django_db
    def test_convert_mp3_models_all_sites(self):
        site1 = factories.SiteFactory.create()
        site2 = factories.SiteFactory.create()

        image1 = self.create_image_model_with_mp3(site1, self.IMAGE_TITLE)
        image2 = self.create_image_model_with_mp3(site2, self.IMAGE_TITLE)
        video1 = self.create_video_model_with_mp3(site1, self.VIDEO_TITLE)
        video2 = self.create_video_model_with_mp3(site2, self.VIDEO_TITLE)

        assert Image.objects.count() == 2
        assert Video.objects.count() == 2

        call_command("convert_mp3_to_audio")

        assert Image.objects.count() == 0
        assert Video.objects.count() == 0
        assert Audio.objects.count() == 4

        converted_image1 = Audio.objects.get(title=self.IMAGE_TITLE, site=site1)
        converted_image2 = Audio.objects.get(title=self.IMAGE_TITLE, site=site2)
        converted_video1 = Audio.objects.get(title=self.VIDEO_TITLE, site=site1)
        converted_video2 = Audio.objects.get(title=self.VIDEO_TITLE, site=site2)

        self.confirm_model_data(image1, converted_image1)
        self.confirm_model_data(image2, converted_image2)
        self.confirm_model_data(video1, converted_video1)
        self.confirm_model_data(video2, converted_video2)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "related_model_factory",
        [
            factories.CharacterFactory,
            factories.DictionaryEntryFactory,
            factories.SongFactory,
            factories.StoryFactory,
        ],
    )
    def test_related_model_links_preserved(self, related_model_factory):
        site = factories.SiteFactory.create()
        image = self.create_image_model_with_mp3(site, self.IMAGE_TITLE)
        video = self.create_video_model_with_mp3(site, self.VIDEO_TITLE)

        related_model_with_image = related_model_factory.create(site=site)
        related_model_with_image.related_images.add(image)

        related_model_with_video = related_model_factory.create(site=site)
        related_model_with_video.related_videos.add(video)

        call_command("convert_mp3_to_audio", site_slug=site.slug)

        converted_image = Audio.objects.get(title=self.IMAGE_TITLE)
        converted_video = Audio.objects.get(title=self.VIDEO_TITLE)

        assert related_model_with_image.related_images.count() == 0
        assert related_model_with_video.related_videos.count() == 0

        related_model_with_image.refresh_from_db()
        related_model_with_video.refresh_from_db()

        assert related_model_with_image.related_audio.count() == 1
        assert related_model_with_video.related_audio.count() == 1
        assert related_model_with_image.related_audio.first() == converted_image
        assert related_model_with_video.related_audio.first() == converted_video

    @pytest.mark.django_db
    def test_related_story_page_links_preserved(self):
        site = factories.SiteFactory.create()
        image = self.create_image_model_with_mp3(site, self.IMAGE_TITLE)
        video = self.create_video_model_with_mp3(site, self.VIDEO_TITLE)

        story = factories.StoryFactory.create(site=site)
        story_page_with_image = factories.StoryPageFactory.create(story=story)
        story_page_with_image.related_images.add(image)

        story_page_with_video = factories.StoryPageFactory.create(story=story)
        story_page_with_video.related_videos.add(video)

        call_command("convert_mp3_to_audio", site_slug=site.slug)

        converted_image = Audio.objects.get(title=self.IMAGE_TITLE)
        converted_video = Audio.objects.get(title=self.VIDEO_TITLE)

        assert story_page_with_image.related_images.count() == 0
        assert story_page_with_video.related_videos.count() == 0

        story_page_with_image.refresh_from_db()
        story_page_with_video.refresh_from_db()

        assert story_page_with_image.related_audio.count() == 1
        assert story_page_with_video.related_audio.count() == 1
        assert story_page_with_image.related_audio.first() == converted_image
        assert story_page_with_video.related_audio.first() == converted_video

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "related_model_factory",
        [
            factories.CharacterFactory,
            factories.DictionaryEntryFactory,
            factories.SongFactory,
            factories.StoryFactory,
        ],
    )
    def test_related_model_links_not_duplicated(self, related_model_factory):
        site = factories.SiteFactory.create()
        image = self.create_image_model_with_mp3(site, self.IMAGE_TITLE)
        video = self.create_video_model_with_mp3(site, self.VIDEO_TITLE)
        audio_with_image_title = factories.AudioFactory.create(
            site=site, title=self.IMAGE_TITLE
        )
        audio_with_video_title = factories.AudioFactory.create(
            site=site, title=self.VIDEO_TITLE
        )

        related_model_with_image = related_model_factory.create(site=site)
        related_model_with_image.related_images.add(image)
        related_model_with_image.related_audio.add(audio_with_image_title)

        related_model_with_video = related_model_factory.create(site=site)
        related_model_with_video.related_videos.add(video)
        related_model_with_video.related_audio.add(audio_with_video_title)

        call_command("convert_mp3_to_audio", site_slug=site.slug)

        assert related_model_with_image.related_images.count() == 0
        assert related_model_with_video.related_videos.count() == 0

        related_model_with_image.refresh_from_db()
        related_model_with_video.refresh_from_db()

        assert related_model_with_image.related_audio.count() == 1
        assert related_model_with_video.related_audio.count() == 1
        assert related_model_with_image.related_audio.first() == audio_with_image_title
        assert related_model_with_video.related_audio.first() == audio_with_video_title

        # duplicate models will be created but will not be linked to related models
        assert Audio.objects.filter(site=site).count() == 4

    @pytest.mark.django_db
    def test_new_file_exists(self):
        site = factories.SiteFactory.create()
        image = self.create_image_model_with_mp3(site, self.IMAGE_TITLE)
        word = factories.DictionaryEntryFactory.create(site=site)
        word.related_images.add(image)

        source_file = image.original.content
        assert os.path.isfile(source_file.path)

        call_command("convert_mp3_to_audio", site_slug=site.slug)

        word.refresh_from_db()
        destination_file = word.related_audio.first().original.content
        assert os.path.isfile(destination_file.path)
