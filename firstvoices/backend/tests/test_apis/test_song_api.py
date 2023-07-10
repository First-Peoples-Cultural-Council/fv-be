import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from ...models import Lyric, Song
from .base_api_test import BaseControlledSiteContentApiTest
from .base_media_test import RelatedMediaTestMixin


class TestSongEndpoint(RelatedMediaTestMixin, BaseControlledSiteContentApiTest):
    """
    End-to-end tests that the song endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:song-list"
    API_DETAIL_VIEW = "api:song-detail"

    model = Song

    def create_minimal_instance(self, site, visibility):
        return factories.SongFactory.create(site=site, visibility=visibility)

    def get_valid_data(self, site=None):
        cover_image = factories.ImageFactory.create(site=site)

        related_images = []
        related_videos = []
        related_audio = []

        for _unused in range(3):
            related_images.append(factories.ImageFactory.create(site=site))
            related_videos.append(factories.VideoFactory.create(site=site))
            related_audio.append(factories.AudioFactory.create(site=site))

        return {
            "relatedAudio": list(map(lambda x: str(x.id), related_audio)),
            "relatedImages": list(map(lambda x: str(x.id), related_images)),
            "relatedVideos": list(map(lambda x: str(x.id), related_videos)),
            "hideOverlay": False,
            "coverImage": str(cover_image.id),
            "title": "Title",
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
        assert str(actual_instance.cover_image.id) == expected_data["coverImage"]

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
        assert actual_response["coverImage"]["id"] == expected_data["coverImage"]

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
            "coverImage": None,
            "titleTranslation": song.title_translation,
            "excludeFromGames": False,
            "excludeFromKids": False,
            "hideOverlay": False,
        }

    def get_expected_list_response_item(self, song, site):
        return self.get_expected_response(song, site)

    def get_expected_response(self, song, site):
        return {
            "created": song.created.astimezone().isoformat(),
            "lastModified": song.last_modified.astimezone().isoformat(),
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
            "url": f"http://testserver{self.get_detail_endpoint(key=song.id, site_slug=site.slug)}",
            "id": str(song.id),
            "hideOverlay": False,
            "title": song.title,
            "site": {
                "id": str(site.id),
                "title": site.title,
                "slug": site.slug,
                "url": f"http://testserver/api/1.0/sites/{site.slug}",
                "language": site.language.title,
                "visibility": "Public",
            },
            "coverImage": None,
            "titleTranslation": song.title_translation,
            "introduction": song.introduction,
            "introductionTranslation": song.introduction_translation,
            "notes": [],
            "lyrics": [],
            "acknowledgements": [],
            "excludeFromGames": False,
            "excludeFromKids": False,
        }

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
