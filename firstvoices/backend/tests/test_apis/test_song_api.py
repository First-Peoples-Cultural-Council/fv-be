import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from ...models import Lyric, Song
from .base_api_test import BaseControlledSiteContentApiTest
from .base_media_test import RelatedMediaTestMixin


class TestSongEndpoint(
    RelatedMediaTestMixin,
    BaseControlledSiteContentApiTest,
):
    """
    End-to-end tests that the song endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:song-list"
    API_DETAIL_VIEW = "api:song-detail"

    model = Song

    def create_minimal_instance(self, site, visibility):
        return factories.SongFactory.create(site=site, visibility=visibility)

    def get_valid_data(self, site=None):
        related_image = factories.ImageFactory.create(site=site)
        related_video = factories.VideoFactory.create(site=site)
        related_audio = factories.AudioFactory.create(site=site)

        return {
            "relatedAudio": [str(related_audio.id)],
            "relatedImages": [str(related_image.id)],
            "relatedVideos": [str(related_video.id)],
            "hideOverlay": False,
            "title": "Title",
            "visibility": "Public",
            "titleTranslation": "A translation of the title",
            "introduction": "introduction",
            "introductionTranslation": "A translation of the introduction",
            "notes": ["Test Note One", "Test Note Two", "Test Note Three"],
            "lyrics": [
                {
                    "text": "First lyrics page",
                    "translation": "Translated 1st",
                },
                {
                    "text": "Second lyrics page",
                    "translation": "Translated 2nd",
                },
                {
                    "text": "Third lyrics page",
                    "translation": "Translated 3rd",
                },
            ],
            "acknowledgements": ["Test Authour", "Another Acknowledgement"],
            "excludeFromGames": True,
            "excludeFromKids": False,
        }

    def assert_updated_instance(self, expected_data, actual_instance: Song):
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.title_translation == expected_data["titleTranslation"]
        assert actual_instance.introduction == expected_data["introduction"]
        assert (
            actual_instance.introduction_translation
            == expected_data["introductionTranslation"]
        )
        assert actual_instance.exclude_from_games == expected_data["excludeFromGames"]
        assert actual_instance.exclude_from_kids == expected_data["excludeFromKids"]
        assert actual_instance.hide_overlay == expected_data["hideOverlay"]
        assert actual_instance.notes[0] == expected_data["notes"][0]
        assert (
            actual_instance.acknowledgements[0] == expected_data["acknowledgements"][0]
        )

        actual_lyrics = Lyric.objects.filter(song__id=actual_instance.id)

        assert len(actual_lyrics) == len(expected_data["lyrics"])

        for index, lyric in enumerate(expected_data["lyrics"]):
            assert lyric["text"] == actual_lyrics[index].text
            assert lyric["translation"] == actual_lyrics[index].translation

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert (
            actual_response["lyrics"][0]["text"] == expected_data["lyrics"][0]["text"]
        )
        assert (
            actual_response["relatedAudio"][0]["id"] == expected_data["relatedAudio"][0]
        )
        assert (
            actual_response["relatedVideos"][0]["id"]
            == expected_data["relatedVideos"][0]
        )
        assert (
            actual_response["relatedImages"][0]["id"]
            == expected_data["relatedImages"][0]
        )

    def assert_created_instance(self, pk, data):
        instance = Song.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def add_related_objects(self, instance):
        factories.LyricsFactory.create(song=instance)
        factories.LyricsFactory.create(song=instance)

    def assert_related_objects_deleted(self, instance):
        for lyric in instance.lyrics.all():
            self.assert_instance_deleted(lyric)

    def create_instance_with_media(
        self,
        site,
        visibility,
        related_images=None,
        related_audio=None,
        related_videos=None,
    ):
        return factories.SongFactory.create(
            site=site,
            visibility=visibility,
            related_images=related_images,
            related_audio=related_audio,
            related_videos=related_videos,
        )

    def get_expected_list_response_item_summary(self, song, site):
        return {
            "url": f"http://testserver{self.get_detail_endpoint(key=song.id, site_slug=site.slug)}",
            "id": str(song.id),
            "title": song.title,
            "visibility": "Public",
            "titleTranslation": song.title_translation,
            "excludeFromGames": False,
            "excludeFromKids": False,
            "hideOverlay": False,
        }

    def get_expected_list_response_item(self, song, site):
        return self.get_expected_response(song, site)

    def get_expected_response(self, instance, site):
        controlled_standard_fields = self.get_expected_controlled_standard_fields(
            instance, site
        )
        return {
            **controlled_standard_fields,
            "hideOverlay": False,
            "titleTranslation": instance.title_translation,
            "introduction": instance.introduction,
            "introductionTranslation": instance.introduction_translation,
            "notes": [],
            "lyrics": [],
            "acknowledgements": [],
            "excludeFromGames": False,
            "excludeFromKids": False,
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
        }

    def create_original_instance_for_patch(self, site):
        audio = factories.AudioFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)
        song = factories.SongFactory.create(
            site=site,
            title="Title",
            title_translation="Title Translation",
            introduction="Introduction",
            introduction_translation="Introduction Translation",
            acknowledgements=["Acknowledgement"],
            notes=["Note"],
            hide_overlay=True,
            exclude_from_games=True,
            exclude_from_kids=True,
            related_audio=(audio,),
            related_images=(image,),
            related_videos=(video,),
        )
        factories.LyricsFactory.create(song=song)
        return song

    def get_valid_patch_data(self, site=None):
        return {"title": "Title Updated"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: Song
    ):
        self.assert_patch_instance_original_fields_related_media(
            original_instance, updated_instance
        )
        assert updated_instance.id == original_instance.id
        assert (
            updated_instance.exclude_from_games == original_instance.exclude_from_games
        )
        assert updated_instance.acknowledgements == original_instance.acknowledgements
        assert updated_instance.hide_overlay == original_instance.hide_overlay
        assert updated_instance.title_translation == original_instance.title_translation
        assert updated_instance.exclude_from_kids == original_instance.exclude_from_kids
        assert updated_instance.notes == original_instance.notes
        assert updated_instance.introduction == original_instance.introduction
        assert (
            updated_instance.introduction_translation
            == original_instance.introduction_translation
        )
        assert updated_instance.lyrics.first() == original_instance.lyrics.first()

    def assert_patch_instance_updated_fields(self, data, updated_instance: Song):
        assert updated_instance.title == data["title"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["title"] == data["title"]
        assert (
            actual_response["titleTranslation"] == original_instance.title_translation
        )
        assert (
            actual_response["excludeFromGames"] == original_instance.exclude_from_games
        )
        assert actual_response["excludeFromKids"] == original_instance.exclude_from_kids
        self.assert_update_patch_response_related_media(
            original_instance, actual_response
        )
        assert actual_response["introduction"] == original_instance.introduction
        assert (
            actual_response["introductionTranslation"]
            == original_instance.introduction_translation
        )
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["hideOverlay"] == original_instance.hide_overlay
        assert (
            actual_response["visibility"] == original_instance.get_visibility_display()
        )
        assert actual_response["notes"][0] == original_instance.notes[0]
        assert (
            actual_response["lyrics"][0]["text"]
            == original_instance.lyrics.first().text
        )
        assert (
            actual_response["acknowledgements"][0]
            == original_instance.acknowledgements[0]
        )

    @pytest.mark.django_db
    def test_lyrics_order(self):
        """Verify lyrics come back in defined order"""

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        song = factories.SongFactory.create(visibility=Visibility.TEAM, site=site)

        lyrics1 = factories.LyricsFactory.create(song=song, ordering=10)
        lyrics2 = factories.LyricsFactory.create(song=song, ordering=20)

        response = self.client.get(
            self.get_detail_endpoint(key=song.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["lyrics"][0]["text"] == lyrics1.text
        assert response_data["lyrics"][1]["text"] == lyrics2.text

    @pytest.mark.django_db
    def test_list_summary(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_list_endpoint(
                site_slug=site.slug, query_kwargs={"summary": "True"}
            )
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][
            0
        ] == self.get_expected_list_response_item_summary(instance, site)
