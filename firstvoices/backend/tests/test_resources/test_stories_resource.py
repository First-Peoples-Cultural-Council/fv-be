import uuid

import pytest
import tablib

from backend.models.constants import Visibility
from backend.models.media import Audio, Image, Video
from backend.models.story import Story, StoryPage
from backend.resources.stories import StoryPageResource, StoryResource
from backend.tests.factories import (
    AudioFactory,
    ImageFactory,
    SiteFactory,
    StoryFactory,
    VideoFactory,
)

sample_draftjs_text = "\"{'entityMap': {}, 'blocks': [{'key': '', 'text': 'Historia de los Tres Osos', 'type': 'unstyled', 'depth': 0, 'inlineStyleRanges': [], 'entityRanges': [], 'data': {}}]}\""  # noqa E501
sample_draftjs_transl = "\"{'entityMap': {}, 'blocks': [{'key': '', 'text': 'History of the Three Bears', 'type': 'unstyled', 'depth': 0, 'inlineStyleRanges': [], 'entityRanges': [], 'data': {}}]}\""  # noqa E501


class TestStoryImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "id,created,created_by,last_modified,last_modified_by,visibility"
            ",title,title_translation,introduction,introduction_translation"
            ",for_games,for_kids_1,for_kids_2,hide_overlay,site,exclude_from_kids,exclude_from_games"
            ",author,notes,acknowledgements,related_audio,related_images,related_videos"
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Story object with basic fields"""
        site = SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,one@test.com,2022-04-06 14:45:52.750,one@test.com,Members"
            f",Testytest,Test story,{sample_draftjs_text},{sample_draftjs_transl}"
            f",,,True,,{site.id},False,False"
            ",By: The Author,,,,,",
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,one@test.com,2022-04-06 14:45:52.750,one@test.com,Members"
            f",Testytest2,Test story two,{sample_draftjs_text},{sample_draftjs_transl}"
            f",,,True,true,{site.id},False,False"
            ",,,,,,",
        ]
        table = self.build_table(data)

        result = StoryResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Story.objects.filter(site=site.id).count() == len(data)

        new_story = Story.objects.get(id=table["id"][0])
        assert new_story.title == table["title"][0]
        assert new_story.visibility == Visibility.MEMBERS
        assert str(new_story.site.id) == table["site"][0]
        assert new_story.title_translation == table["title_translation"][0]
        assert new_story.introduction == table["introduction"][0]
        assert (
            new_story.introduction_translation == table["introduction_translation"][0]
        )
        assert new_story.hide_overlay is False  # csv is null
        assert str(new_story.exclude_from_kids) == table["exclude_from_kids"][0]
        assert str(new_story.exclude_from_games) == table["exclude_from_games"][0]
        assert new_story.author == table["author"][0]
        assert new_story.related_audio.all().count() == 0
        assert new_story.related_images.all().count() == 0
        assert new_story.related_videos.all().count() == 0

        # other possible hide-overlay value
        new_story = Story.objects.get(id=table["id"][1])
        assert new_story.hide_overlay is True  # csv is "true"

    @pytest.mark.parametrize(
        "note_string,ack_string,expected_len",
        [
            ("Note about stuff", "Thanks Everyone", 1),
            ("Note1|||Note2|||Note3", "Thanks Me|||Thanks You|||Thanks All", 3),
            ('"Note, Comma|||  Note2"', '"Thanks, Comma|||Thanks2"', 2),
        ],
    )
    @pytest.mark.django_db
    def test_import_array_fields(self, note_string, ack_string, expected_len):
        """Import Story object with array fields for notes, acks"""
        site = SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,one@test.com,2022-04-06 14:45:52.750,one@test.com,Members"
            f",Testytest,Test story,,"
            f",,,True,,{site.id},False,False"
            f",Authorname,{note_string},{ack_string},,,"
        ]
        table = self.build_table(data)

        result = StoryResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Story.objects.filter(site=site.id).count() == len(data)

        new_story = Story.objects.get(id=table["id"][0])
        assert len(new_story.notes) == expected_len
        assert len(new_story.acknowledgements) == expected_len

        assert all(note.startswith("Note") for note in new_story.notes)
        assert all(ack.startswith("Thanks") for ack in new_story.acknowledgements)

    @pytest.mark.django_db
    def test_import_related_media(self):
        """Import Story object with already loaded related media"""
        site = SiteFactory.create()
        audio = AudioFactory.create(site=site)
        img_1 = ImageFactory.create(site=site)
        img_2 = ImageFactory.create(site=site)
        video = VideoFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,one@test.com,2022-04-06 14:45:52.750,one@test.com,Members"
            f",Testytest,Test story,,"
            f",,,True,,{site.id},False,False"
            f',Authorname,,,{audio.id},"{img_1.id},{img_2.id}",{video.id}'
        ]
        table = self.build_table(data)

        result = StoryResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Story.objects.filter(site=site.id).count() == len(data)

        new_story = Story.objects.get(id=table["id"][0])
        # single audio, video
        assert audio in new_story.related_audio.all()
        assert new_story.related_audio.all().count() == 1
        assert video in new_story.related_videos.all()
        assert new_story.related_videos.all().count() == 1
        # multiple images
        assert img_1 in new_story.related_images.all()
        assert img_2 in new_story.related_images.all()
        assert new_story.related_images.all().count() == 2

    @pytest.mark.django_db
    def test_import_related_media_skip_nonexistent(self):
        """Import Story object successfully if related media are not found"""
        site = SiteFactory.create()
        img_1 = ImageFactory.create(site=site)
        no_audio_here = uuid.uuid4()
        no_img_here = uuid.uuid4()
        no_video_here = uuid.uuid4()
        data = [
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,one@test.com,2022-04-06 14:45:52.750,one@test.com,Members"
            f",Testytest,Test story,,"
            f",,,True,,{site.id},False,False"
            f',Authorname,,,{no_audio_here},"{img_1.id},{no_img_here}",{no_video_here}'
        ]
        table = self.build_table(data)

        result = StoryResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Story.objects.filter(site=site.id).count() == len(data)

        new_story = Story.objects.get(id=table["id"][0])
        # no audio, video found
        assert new_story.related_audio.all().count() == 0
        assert Audio.objects.filter(id=no_audio_here).count() == 0
        assert new_story.related_videos.all().count() == 0
        assert Video.objects.filter(id=no_video_here).count() == 0
        # 1 of multiple images found
        assert img_1 in new_story.related_images.all()
        assert new_story.related_images.all().count() == 1
        assert Image.objects.filter(id=no_img_here).count() == 0


class TestStoryPageImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "id,created,created_by,last_modified,last_modified_by,parent_id"
            ",text,ordering,site,translation,notes,related_audio,related_images,related_videos"
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import StoryPage object with basic fields"""
        site = SiteFactory.create()
        story = StoryFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,one@test.com,2022-04-06 14:45:52.750,one@test.com,{story.id}"
            f",{sample_draftjs_text},0,{site.id},{sample_draftjs_transl},,,,",
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,two@test.com,2022-04-06 14:45:52.750,two@test.com,{story.id}"
            f",{sample_draftjs_text},1,{site.id},{sample_draftjs_transl},,,,",
        ]
        table = self.build_table(data)

        result = StoryPageResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)

        assert StoryPage.objects.filter(site=site.id).count() == len(data)
        assert StoryPage.objects.filter(story=story.id).count() == len(data)

        new_page = StoryPage.objects.get(id=table["id"][0])
        assert str(new_page.site.id) == table["site"][0]
        assert str(new_page.ordering) == table["ordering"][0]
        assert new_page.text == table["text"][0]
        assert new_page.translation == table["translation"][0]
        assert new_page.related_audio.all().count() == 0
        assert new_page.related_images.all().count() == 0
        assert new_page.related_videos.all().count() == 0
        assert new_page.visibility == story.visibility

    @pytest.mark.django_db
    def test_skip_song_lyrics(self):
        """Ensure song lyric objects are skipped"""
        site = SiteFactory.create()
        no_id_here = uuid.uuid4()
        data = [
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,one@test.com,2022-04-06 14:45:52.750,one@test.com,{no_id_here}"
            f",{sample_draftjs_text},0,{site.id},{sample_draftjs_transl},,,,",
        ]
        table = self.build_table(data)

        result = StoryPageResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["skip"] == len(data)

    @pytest.mark.parametrize(
        "note_string,expected_len",
        [
            ("   Note about stuff", 1),
            ("Note1|||Note2|||Note3", 3),
            ('"Note, Comma, Note ||| Note2"', 2),
        ],
    )
    @pytest.mark.django_db
    def test_import_array_fields(self, note_string, expected_len):
        """Import StoryPage object with array field for notes"""
        site = SiteFactory.create()
        story = StoryFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,one@test.com,2022-04-06 14:45:52.750,one@test.com,{story.id}"
            f",{sample_draftjs_text},0,{site.id},{sample_draftjs_transl},{note_string},,,",
        ]
        table = self.build_table(data)

        result = StoryPageResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert StoryPage.objects.filter(site=site.id).count() == len(data)

        new_page = StoryPage.objects.get(id=table["id"][0])
        assert len(new_page.notes) == expected_len
        assert all(note.startswith("Note") for note in new_page.notes)

    @pytest.mark.django_db
    def test_import_related_media(self):
        """Import Story object with already loaded related media"""
        site = SiteFactory.create()
        story = StoryFactory.create(site=site)

        audio = AudioFactory.create(site=site)
        img_1 = ImageFactory.create(site=site)
        img_2 = ImageFactory.create(site=site)
        video = VideoFactory.create(site=site)

        data = [
            f"{uuid.uuid4()},2022-04-06 14:08:27.693,one@test.com,2022-04-06 14:45:52.750,one@test.com,{story.id}"
            f',{sample_draftjs_text},0,{site.id},{sample_draftjs_transl},,{audio.id},"{img_1.id},{img_2.id}",{video.id}'
        ]
        table = self.build_table(data)

        result = StoryPageResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert StoryPage.objects.filter(site=site.id).count() == len(data)

        new_page = StoryPage.objects.get(id=table["id"][0])
        # single audio, video
        assert audio in new_page.related_audio.all()
        assert new_page.related_audio.all().count() == 1
        assert video in new_page.related_videos.all()
        assert new_page.related_videos.all().count() == 1
        # multiple images
        assert img_1 in new_page.related_images.all()
        assert img_2 in new_page.related_images.all()
        assert new_page.related_images.all().count() == 2
