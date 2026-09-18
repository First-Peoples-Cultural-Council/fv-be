import json

import pytest

from backend.models.constants import Visibility
from backend.search.constants import (
    TYPE_AUDIO,
    TYPE_DOCUMENT,
    TYPE_IMAGE,
    TYPE_PHRASE,
    TYPE_SONG,
    TYPE_STORY,
    TYPE_VIDEO,
    TYPE_WORD,
)
from backend.tests import factories
from backend.tests.test_apis.base.base_non_site_api import (
    BaseNonSiteApiTest,
    NonSiteDetailEndpointTestMixin,
)


class TestLookupApi(NonSiteDetailEndpointTestMixin, BaseNonSiteApiTest):
    """
    Tests for the UUID lookup endpoint, which resolves an object of any supported
    type from its id alone.
    """

    API_DETAIL_VIEW = "api:lookup-detail"

    def create_public_site(self):
        return factories.SiteFactory.create(visibility=Visibility.PUBLIC)

    @pytest.mark.django_db
    def test_lookup_word(self):
        site = self.create_public_site()
        entry = factories.DictionaryEntryFactory.create(
            site=site, type=TYPE_WORD, visibility=Visibility.PUBLIC
        )

        response = self.client.get(self.get_detail_endpoint(key=entry.id))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(entry.id)
        assert response_data["type"] == TYPE_WORD

    @pytest.mark.django_db
    def test_lookup_phrase(self):
        site = self.create_public_site()
        entry = factories.DictionaryEntryFactory.create(
            site=site, type=TYPE_PHRASE, visibility=Visibility.PUBLIC
        )

        response = self.client.get(self.get_detail_endpoint(key=entry.id))

        assert response.status_code == 200
        assert json.loads(response.content)["type"] == TYPE_PHRASE

    @pytest.mark.django_db
    def test_lookup_song(self):
        site = self.create_public_site()
        song = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=song.id))

        assert response.status_code == 200
        assert json.loads(response.content)["type"] == TYPE_SONG

    @pytest.mark.django_db
    def test_lookup_story(self):
        site = self.create_public_site()
        story = factories.StoryFactory.create(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=story.id))

        assert response.status_code == 200
        assert json.loads(response.content)["type"] == TYPE_STORY

    @pytest.mark.django_db
    def test_lookup_audio(self):
        site = self.create_public_site()
        audio = factories.AudioFactory.create(site=site)

        response = self.client.get(self.get_detail_endpoint(key=audio.id))

        assert response.status_code == 200
        assert json.loads(response.content)["type"] == TYPE_AUDIO

    @pytest.mark.django_db
    def test_lookup_document(self):
        site = self.create_public_site()
        document = factories.DocumentFactory.create(site=site)

        response = self.client.get(self.get_detail_endpoint(key=document.id))

        assert response.status_code == 200
        assert json.loads(response.content)["type"] == TYPE_DOCUMENT

    @pytest.mark.django_db
    def test_lookup_image(self):
        site = self.create_public_site()
        image = factories.ImageFactory.create(site=site)

        response = self.client.get(self.get_detail_endpoint(key=image.id))

        assert response.status_code == 200
        assert json.loads(response.content)["type"] == TYPE_IMAGE

    @pytest.mark.django_db
    def test_lookup_video(self):
        site = self.create_public_site()
        video = factories.VideoFactory.create(site=site)

        response = self.client.get(self.get_detail_endpoint(key=video.id))

        assert response.status_code == 200
        assert json.loads(response.content)["type"] == TYPE_VIDEO

    @pytest.mark.django_db
    def test_url_points_to_detail_route(self):
        site = self.create_public_site()
        song = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=song.id))

        response_data = json.loads(response.content)
        assert site.slug in response_data["url"]
        assert str(song.id) in response_data["url"]

    @pytest.mark.django_db
    def test_site_shape(self):
        site = self.create_public_site()
        song = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=song.id))

        site_data = json.loads(response.content)["site"]
        assert set(site_data.keys()) == {
            "id",
            "slug",
            "title",
            "visibility",
            "isHidden",
        }

    @pytest.mark.django_db
    def test_response_is_flat(self):
        site = self.create_public_site()
        song = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=song.id))

        response_data = json.loads(response.content)
        assert "entry" not in response_data
        assert "searchResultId" not in response_data

    @pytest.mark.django_db
    def test_404_unknown_uuid(self):
        response = self.client.get(
            self.get_detail_endpoint(key="00000000-0000-0000-0000-000000000000")
        )
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_404_malformed_uuid(self):
        response = self.client.get(self.get_detail_endpoint(key="not-a-uuid"))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_anonymouse_user_can_see_public_object(self):
        site = self.create_public_site()
        song = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=song.id))

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_anonymouse_response_omits_by_fields(self):
        site = self.create_public_site()
        song = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=song.id))

        response_data = json.loads(response.content)
        assert "createdBy" not in response_data
        assert "lastModifiedBy" not in response_data
        assert "systemLastModifiedBy" not in response_data

    @pytest.mark.django_db
    def test_authenticated_response_has_all_fields(self):
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        site = self.create_public_site()
        song = factories.SongFactory.create(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=song.id))

        response_data = json.loads(response.content)
        assert set(response_data.keys()) == {
            "id",
            "type",
            "title",
            "url",
            "site",
            "created",
            "createdBy",
            "lastModified",
            "lastModifiedBy",
            "systemLastModified",
            "systemLastModifiedBy",
        }

    @pytest.mark.django_db
    def test_401_anonymouse_user_non_public_object(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        song = factories.SongFactory.create(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_detail_endpoint(key=song.id))

        assert response.status_code == 401

    @pytest.mark.django_db
    def test_403_user_without_permission(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        song = factories.SongFactory.create(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_detail_endpoint(key=song.id))

        assert response.status_code == 403
