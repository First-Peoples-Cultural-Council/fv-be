import json

import pytest
from rest_framework.reverse import reverse

from backend.models.constants import Role, Visibility
from backend.models.story import StoryPage
from backend.tests import factories

from .base_api_test import BaseControlledSiteContentApiTest
from .base_media_test import (
    MOCK_EMBED_LINK,
    MOCK_THUMBNAIL_LINK,
    VIMEO_VIDEO_LINK,
    YOUTUBE_VIDEO_LINK,
    RelatedMediaTestMixin,
)


class TestStoryPageEndpoint(RelatedMediaTestMixin, BaseControlledSiteContentApiTest):
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
        related_video_links=None,
    ):
        if related_video_links is None:
            related_video_links = []
        story = factories.StoryFactory(site=site, visibility=visibility)
        return factories.StoryPageFactory.create(
            site=site,
            story=story,
            related_images=related_images,
            related_audio=related_audio,
            related_videos=related_videos,
            related_video_links=related_video_links,
        )

    def get_valid_data(self, site=None):
        return {
            "relatedAudio": [str(factories.AudioFactory.create(site=site).id)],
            "relatedImages": [str(factories.ImageFactory.create(site=site).id)],
            "relatedVideos": [str(factories.VideoFactory.create(site=site).id)],
            "relatedVideoLinks": [],
            "text": "Title",
            "translation": "A translation of the title",
            "notes": [
                {"text": "Test Note One"},
                {"text": "Test Note Two"},
                {"text": "Test Note Three"},
            ],
            "ordering": 99,
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "text": "Title",
            "ordering": 8,
        }

    def add_expected_defaults(self, data):
        return {
            **data,
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
            "relatedVideoLinks": [],
            "translation": "",
            "notes": [],
        }

    def create_original_instance_for_patch(self, site):
        audio = factories.AudioFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)
        story = factories.StoryFactory.create(site=site)
        return factories.StoryPageFactory.create(
            site=site,
            story=story,
            ordering=1,
            text="Text",
            translation="Translation",
            notes=["Note"],
            related_audio=(audio,),
            related_images=(image,),
            related_videos=(video,),
            related_video_links=[YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK],
        )

    def get_valid_patch_data(self, site=None):
        return {"text": "Text Updated"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: StoryPage
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.translation == original_instance.translation
        assert updated_instance.ordering == original_instance.ordering
        assert updated_instance.notes == original_instance.notes
        self.assert_patch_instance_original_fields_related_media(
            original_instance, updated_instance
        )
        assert updated_instance.story == original_instance.story
        assert (
            updated_instance.related_video_links
            == original_instance.related_video_links
        )

    def assert_patch_instance_updated_fields(self, data, updated_instance: StoryPage):
        assert updated_instance.text == data["text"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        self.assert_update_patch_response_related_media(
            original_instance, actual_response
        )
        assert actual_response["text"] == data["text"]
        assert actual_response["translation"] == original_instance.translation
        assert actual_response["notes"][0]["text"] == original_instance.notes[0]
        assert actual_response["ordering"] == original_instance.ordering
        assert actual_response["story"]["id"] == str(original_instance.story.id)
        assert actual_response["relatedVideoLinks"] == [
            {
                "videoLink": original_instance.related_video_links[0],
                "embedLink": MOCK_EMBED_LINK,
                "thumbnail": MOCK_THUMBNAIL_LINK,
            },
            {
                "videoLink": original_instance.related_video_links[1],
                "embedLink": MOCK_EMBED_LINK,
                "thumbnail": MOCK_THUMBNAIL_LINK,
            },
        ]

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

    @pytest.mark.django_db
    def test_create_with_nulls_success_201(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        story = factories.StoryFactory.create(site=site, visibility=site.visibility)
        data = self.get_valid_data_with_nulls(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug, story_id=str(story.id)),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

        response_data = json.loads(response.content)
        pk = response_data["id"]

        expected_data = self.add_expected_defaults(data)
        self.assert_created_instance(pk, expected_data)
        self.assert_created_response(expected_data, response_data)

    def assert_created_instance(self, pk, data):
        instance = StoryPage.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def assert_updated_instance(self, expected_data, actual_instance: StoryPage):
        assert actual_instance.text == expected_data["text"]
        assert actual_instance.translation == expected_data["translation"]
        assert actual_instance.ordering == expected_data["ordering"]

        assert len(expected_data["notes"]) == len(actual_instance.notes)
        for i, n in enumerate(expected_data["notes"]):
            assert actual_instance.notes[i] == n["text"]

        assert len(actual_instance.related_audio.all()) == len(
            expected_data["relatedAudio"]
        )
        for i, item in enumerate(expected_data["relatedAudio"]):
            assert str(actual_instance.related_audio.all()[i].id) == item

        assert len(actual_instance.related_images.all()) == len(
            expected_data["relatedImages"]
        )
        for i, item in enumerate(expected_data["relatedImages"]):
            assert str(actual_instance.related_images.all()[i].id) == item

        assert len(actual_instance.related_videos.all()) == len(
            expected_data["relatedVideos"]
        )
        for i, item in enumerate(expected_data["relatedVideos"]):
            assert str(actual_instance.related_videos.all()[i].id) == item

        assert actual_instance.related_video_links == expected_data["relatedVideoLinks"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["text"] == expected_data["text"]
        assert actual_response["translation"] == expected_data["translation"]

        for i, note in enumerate(expected_data["notes"]):
            assert actual_response["notes"][i]["text"] == note["text"]

        assert len(actual_response["relatedAudio"]) == len(
            expected_data["relatedAudio"]
        )
        for i, a in enumerate(expected_data["relatedAudio"]):
            assert actual_response["relatedAudio"][i]["id"] == a

        assert len(actual_response["relatedVideos"]) == len(
            expected_data["relatedVideos"]
        )
        for i, v in enumerate(expected_data["relatedVideos"]):
            assert actual_response["relatedVideos"][i]["id"] == v

        assert len(actual_response["relatedImages"]) == len(
            expected_data["relatedImages"]
        )
        for i, img in enumerate(expected_data["relatedImages"]):
            assert actual_response["relatedImages"][i]["id"] == img

        assert (
            actual_response["relatedVideoLinks"] == expected_data["relatedVideoLinks"]
        )

    def add_related_objects(self, instance):
        # nothing to add
        pass

    def assert_related_objects_deleted(self, instance):
        # nothing to delete
        pass

    def get_expected_response(self, instance, site):
        story_url = reverse(
            "api:story-detail",
            current_app=self.APP_NAME,
            args=[site.slug, str(instance.story.id)],
        )

        return {
            "created": instance.created.astimezone().isoformat(),
            "createdBy": instance.created_by.email,
            "lastModified": instance.last_modified.astimezone().isoformat(),
            "lastModifiedBy": instance.last_modified_by.email,
            "id": str(instance.id),
            "url": f"http://testserver{self.get_detail_endpoint(key=instance.id, site_slug=site.slug)}",
            "text": instance.text,
            "translation": instance.translation,
            "notes": instance.notes,
            "ordering": instance.ordering,
            "story": {
                "id": str(instance.story.id),
                "title": instance.story.title,
                "url": f"http://testserver{story_url}",
            },
            "site": {
                "id": str(site.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}",
                "title": site.title,
                "slug": site.slug,
                "visibility": instance.site.get_visibility_display().lower(),
                "language": site.language.title,
            },
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
            "relatedVideoLinks": [],
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

    @pytest.mark.django_db
    def test_create_assistant_permissions_valid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(site=site, visibility=Visibility.TEAM)
        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug, story_id=str(story.id)),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

    @pytest.mark.django_db
    def test_create_assistant_permissions_invalid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug, story_id=str(story.id)),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_update_assistant_permissions_valid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_update_assistant_permissions_invalid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_list_permissions(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        self.create_minimal_instance(site=site, visibility=Visibility.MEMBERS)
        self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug, story_id=str(instance.story_id))
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance, site
        )
