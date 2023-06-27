import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from .base_api_test import BaseReadOnlyControlledSiteContentApiTest
from .base_media_test import RelatedMediaTestMixin


class TestSongEndpoint(RelatedMediaTestMixin, BaseReadOnlyControlledSiteContentApiTest):
    """
    End-to-end tests that the song endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:song-list"
    API_DETAIL_VIEW = "api:song-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.SongFactory.create(site=site, visibility=visibility)

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

    def get_expected_list_response_item(self, song, site):
        return {
            "url": f"http://testserver{self.get_detail_endpoint(key=song.id, site_slug=site.slug)}",
            "id": str(song.id),
            "title": song.title,
        }

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
