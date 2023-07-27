import json

import pytest
from rest_framework.reverse import reverse

from backend.models.constants import Role, Visibility
from backend.models.story import StoryPage
from backend.tests import factories

from .base_api_test import BaseUncontrolledSiteContentApiTest
from .base_media_test import RelatedMediaTestMixin


class TestStoryPageEndpoint(RelatedMediaTestMixin, BaseUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the story page endpoints have the expected behaviour.
    Most of the tests have been overridden here because of the extra-nested url structure.
    """

    API_LIST_VIEW = "api:storypage-list"
    API_DETAIL_VIEW = "api:storypage-detail"
    model = StoryPage

    def get_list_endpoint(self, site_slug, story_id):
        # nested url needs both site and story
        url = reverse(
            self.API_LIST_VIEW, current_app=self.APP_NAME, args=[site_slug, story_id]
        )
        return url

    def get_detail_endpoint(self, key, site_slug):
        # look up the story for the nested url
        story_id = "123-fake-id"

        try:
            instance = StoryPage.objects.get(pk=key)
            story_id = str(instance.story_id)
        except Exception:
            # use the fake story id if we aren't using a real site here
            pass

        return reverse(
            self.API_DETAIL_VIEW,
            current_app=self.APP_NAME,
            args=[site_slug, story_id, str(key)],
        )

    def create_minimal_instance(self, site, visibility):
        story = factories.StoryFactory(site=site, visibility=visibility)
        return factories.StoryPageFactory.create(site=site, story=story)

    def create_instance_with_media(
        self,
        site,
        visibility,
        related_images=None,
        related_audio=None,
        related_videos=None,
    ):
        story = factories.StoryFactory(site=site, visibility=visibility)
        return factories.StoryPageFactory.create(
            site=site,
            story=story,
            related_images=related_images,
            related_audio=related_audio,
            related_videos=related_videos,
        )

    def get_valid_data(self, site=None):
        return {
            "relatedAudio": [str(factories.AudioFactory.create(site=site).id)],
            "relatedImages": [str(factories.ImageFactory.create(site=site).id)],
            "relatedVideos": [str(factories.VideoFactory.create(site=site).id)],
            "text": "Title",
            "translation": "A translation of the title",
            "notes": ["Test Note One", "Test Note Two", "Test Note Three"],
            "ordering": 99,
        }

    @pytest.mark.django_db
    def test_list_404_site_not_found(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(
                site_slug="missing-site", story_id="missing-story-id"
            )
        )

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.django_db
    def test_list_403_site_not_visible(self, visibility):
        site = self.create_site_with_non_member(visibility)
        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug, story_id="missing-story-id")
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_list_empty(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        story = factories.StoryFactory.create(site=site, visibility=site.visibility)
        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug, story_id=str(story.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_list_member_access(self, role):
        # tests member access to the site
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(site=site, visibility=site.visibility)

        response = self.client.get(
            self.get_list_endpoint(site.slug, story_id=str(story.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_list_member_access_to_story(self, role):
        # tests member access to the site
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(site=site, visibility=Visibility.MEMBERS)

        response = self.client.get(
            self.get_list_endpoint(site.slug, story_id=str(story.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_list_team_access(self):
        # tests team access to site
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(site=site, visibility=site.visibility)

        response = self.client.get(
            self.get_list_endpoint(site.slug, story_id=str(story.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_list_team_access_to_story(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(site=site, visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_list_endpoint(site.slug, story_id=str(story.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_list_minimal(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        page = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug, story_id=str(page.story.id))
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            page, site
        )

    @pytest.mark.django_db
    def test_create_invalid_400(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        story = factories.StoryFactory.create(site=site, visibility=site.visibility)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug, story_id=str(story.id)),
            data=self.format_upload_data(self.get_invalid_data()),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_create_private_site_403(self):
        site = self.create_site_with_non_member(Visibility.MEMBERS)
        story = factories.StoryFactory.create(site=site, visibility=site.visibility)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug, story_id=str(story.id)),
            data=self.format_upload_data(self.get_valid_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_create_site_missing_404(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        response = self.client.post(
            self.get_list_endpoint(site_slug="missing-site", story_id="missing-story"),
            data=self.format_upload_data(self.get_valid_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_create_story_missing_404(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug, story_id="missing-story"),
            data=self.format_upload_data(self.get_valid_data(site)),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_create_success_201(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        story = factories.StoryFactory.create(site=site, visibility=site.visibility)
        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug, story_id=str(story.id)),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

        response_data = json.loads(response.content)
        pk = response_data["id"]

        self.assert_created_instance(pk, data)
        self.assert_created_response(data, response_data)

    def assert_created_instance(self, pk, data):
        instance = StoryPage.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def assert_updated_instance(self, expected_data, actual_instance: StoryPage):
        assert actual_instance.text == expected_data["text"]
        assert actual_instance.translation == expected_data["translation"]
        assert actual_instance.ordering == expected_data["ordering"]
        assert actual_instance.notes == expected_data["notes"]
        assert (
            str(actual_instance.related_audio.first().id)
            == expected_data["relatedAudio"][0]
        )
        assert (
            str(actual_instance.related_images.first().id)
            == expected_data["relatedImages"][0]
        )
        assert (
            str(actual_instance.related_videos.first().id)
            == expected_data["relatedVideos"][0]
        )

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["text"] == expected_data["text"]
        assert actual_response["translation"] == expected_data["translation"]
        assert actual_response["notes"] == expected_data["notes"]
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

    def add_related_objects(self, instance):
        pass

    def assert_related_objects_deleted(self, instance):
        pass

    def get_expected_response(self, instance, site):
        story_url = reverse(
            "api:story-detail",
            current_app=self.APP_NAME,
            args=[site.slug, str(instance.story.id)],
        )

        return {
            "url": f"http://testserver{self.get_detail_endpoint(key=instance.id, site_slug=site.slug)}",
            "id": str(instance.id),
            "text": instance.text,
            "translation": instance.translation,
            "notes": instance.notes,
            "ordering": instance.ordering,
            "story": {
                "id": str(instance.story.id),
                "title": instance.story.title,
                "url": f"http://testserver{story_url}",
            },
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
        }

    @pytest.mark.django_db
    def test_detail_404_story_not_found(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug="invalid")
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_detail_403_story_not_visible(self):
        site = self.create_site_with_non_member(Visibility.MEMBERS)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 403
