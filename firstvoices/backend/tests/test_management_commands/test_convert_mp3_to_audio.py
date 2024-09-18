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
