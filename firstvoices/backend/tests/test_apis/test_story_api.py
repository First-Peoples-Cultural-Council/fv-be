import json

import pytest

from backend.models.constants import Role, Visibility
from backend.models.story import Story, StoryPage
from backend.tests import factories

from .base_api_test import BaseControlledSiteContentApiTest
from .base_media_test import RelatedMediaTestMixin


class TestStoryEndpoint(
    RelatedMediaTestMixin,
    BaseControlledSiteContentApiTest,
):
    """
    End-to-end tests that the story endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:story-list"
    API_DETAIL_VIEW = "api:story-detail"

    model = Story

    def create_minimal_instance(self, site, visibility):
        return factories.StoryFactory.create(site=site, visibility=visibility)

    def get_valid_data(self, site=None):
        images = []
        videos = []
        audio = []

        for _ in range(3):
            images.append(factories.ImageFactory.create(site=site))
            videos.append(factories.VideoFactory.create(site=site))
            audio.append(factories.AudioFactory.create(site=site))

        return {
            "relatedAudio": [str(x.id) for x in audio],
            "relatedImages": [str(x.id) for x in images],
            "relatedVideos": [str(x.id) for x in videos],
            "visibility": "Public",
            "title": "Title",
            "titleTranslation": "A translation of the title",
            "introduction": "introduction",
            "introductionTranslation": "A translation of the introduction",
            "notes": [
                {"id": 1, "text": "Test Note One"},
                {"id": "5", "text": "Test Note Two"},
                {"id": "2", "text": "Test Note Three"},
            ],
            "acknowledgements": [
                {"id": "5", "text": "Test Author"},
                {"id": "51", "text": "Another Acknowledgement"},
            ],
            "pages": [],
            "excludeFromGames": True,
            "excludeFromKids": False,
            "author": "Dr. Author",
            "hideOverlay": True,
        }

    def assert_updated_instance(self, expected_data, actual_instance: Story):
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.title_translation == expected_data["titleTranslation"]
        assert actual_instance.introduction == expected_data["introduction"]
        assert (
            actual_instance.introduction_translation
            == expected_data["introductionTranslation"]
        )
        assert actual_instance.exclude_from_games == expected_data["excludeFromGames"]
        assert actual_instance.exclude_from_kids == expected_data["excludeFromKids"]
        assert actual_instance.notes[0] == expected_data["notes"][0]["text"]
        assert (
            actual_instance.acknowledgements[0]
            == expected_data["acknowledgements"][0]["text"]
        )

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]

        response_related_audio_ids = [i["id"] for i in actual_response["relatedAudio"]]
        response_related_image_ids = [i["id"] for i in actual_response["relatedImages"]]
        response_related_video_ids = [i["id"] for i in actual_response["relatedVideos"]]

        assert sorted(response_related_audio_ids) == sorted(
            expected_data["relatedAudio"]
        )
        assert sorted(response_related_image_ids) == sorted(
            expected_data["relatedImages"]
        )
        assert sorted(response_related_video_ids) == sorted(
            expected_data["relatedVideos"]
        )

        assert actual_response["pages"] == []  # unchanged

    def assert_created_instance(self, pk, data):
        instance = Story.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def add_related_objects(self, instance):
        factories.StoryPageFactory.create(story=instance)
        factories.StoryPageFactory.create(story=instance)

    def assert_related_objects_deleted(self, instance):
        assert instance.pages.count() == 0

    def create_instance_with_media(
        self,
        site,
        visibility,
        related_images=None,
        related_audio=None,
        related_videos=None,
    ):
        return factories.StoryFactory.create(
            site=site,
            visibility=visibility,
            related_images=related_images,
            related_audio=related_audio,
            related_videos=related_videos,
        )

    def get_expected_list_response_item(self, instance, site):
        controlled_standard_fields = self.get_expected_controlled_standard_fields(
            instance, site
        )
        return {
            **controlled_standard_fields,
            "titleTranslation": instance.title_translation,
            "excludeFromGames": False,
            "excludeFromKids": False,
            "hideOverlay": instance.hide_overlay,
        }

    def get_expected_response(self, instance, site):
        controlled_standard_fields = self.get_expected_controlled_standard_fields(
            instance, site
        )
        return {
            **controlled_standard_fields,
            "titleTranslation": instance.title_translation,
            "introduction": instance.introduction,
            "introductionTranslation": instance.introduction_translation,
            "notes": [],
            "pages": [],
            "acknowledgements": [],
            "excludeFromGames": instance.exclude_from_games,
            "excludeFromKids": instance.exclude_from_kids,
            "author": instance.author,
            "hideOverlay": instance.hide_overlay,
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
        }

    def create_original_instance_for_patch(self, site):
        audio = factories.AudioFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)
        story = factories.StoryFactory.create(
            site=site,
            author="Author",
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
        factories.StoryPageFactory.create(site=site, story=story)
        return story

    def get_valid_patch_data(self, site=None):
        return {"title": "Title Updated"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: Story
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.title_translation == original_instance.title_translation
        assert updated_instance.introduction == original_instance.introduction
        assert (
            updated_instance.introduction_translation
            == original_instance.introduction_translation
        )
        assert updated_instance.acknowledgements == original_instance.acknowledgements
        assert updated_instance.notes == original_instance.notes
        assert updated_instance.hide_overlay == original_instance.hide_overlay
        assert (
            updated_instance.exclude_from_games == original_instance.exclude_from_games
        )
        assert updated_instance.exclude_from_kids == original_instance.exclude_from_kids
        self.assert_patch_instance_original_fields_related_media(
            original_instance, updated_instance
        )
        assert updated_instance.pages.first() == original_instance.pages.first()

    def assert_patch_instance_updated_fields(self, data, updated_instance: Story):
        assert updated_instance.title == data["title"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["title"] == data["title"]
        self.assert_update_patch_response_related_media(
            original_instance, actual_response
        )
        assert actual_response["hideOverlay"] == original_instance.hide_overlay
        assert (
            actual_response["visibility"]
            == original_instance.get_visibility_display().lower()
        )
        assert (
            actual_response["titleTranslation"] == original_instance.title_translation
        )
        assert actual_response["introduction"] == original_instance.introduction
        assert (
            actual_response["introductionTranslation"]
            == original_instance.introduction_translation
        )
        assert actual_response["notes"][0]["text"] == original_instance.notes[0]
        assert (
            actual_response["pages"][0]["text"] == original_instance.pages.first().text
        )
        assert (
            actual_response["acknowledgements"][0]["text"]
            == original_instance.acknowledgements[0]
        )
        assert (
            actual_response["excludeFromGames"] == original_instance.exclude_from_games
        )
        assert actual_response["excludeFromKids"] == original_instance.exclude_from_kids

    @pytest.mark.django_db
    def test_pages_order(self):
        """Verify pages come back in defined order"""

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(visibility=Visibility.TEAM, site=site)

        page1 = factories.StoryPageFactory.create(story=story, ordering=10)
        page2 = factories.StoryPageFactory.create(story=story, ordering=20)

        response = self.client.get(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["pages"][0]["text"] == page1.text
        assert response_data["pages"][1]["text"] == page2.text

    @pytest.mark.django_db
    def test_update_page_order(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(visibility=Visibility.PUBLIC, site=site)

        page1 = factories.StoryPageFactory.create(
            visibility=Visibility.PUBLIC, story=story, ordering=0
        )
        page2 = factories.StoryPageFactory.create(
            visibility=Visibility.PUBLIC, story=story, ordering=1
        )

        assert Story.objects.filter(site=site).count() == 1
        assert StoryPage.objects.all().count() == 2
        assert StoryPage.objects.filter(story=story).count() == 2
        assert StoryPage.objects.get(id=page1.id).ordering == 0
        assert StoryPage.objects.get(id=page2.id).ordering == 1

        response = self.client.get(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["pages"][0]["text"] == page1.text
        assert response_data["pages"][1]["text"] == page2.text

        data = {
            "title": story.title,
            "visibility": story.get_visibility_display(),
            "author": "",
            "title_translation": "",
            "introduction": "",
            "introduction_translation": "",
            "notes": [],
            "pages": [str(page2.id), str(page1.id)],
            "acknowledgements": [],
            "hide_overlay": False,
            "exclude_from_games": False,
            "exclude_from_kids": False,
            "related_audio": [],
            "related_images": [],
            "related_videos": [],
        }

        response = self.client.put(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug),
            data=json.dumps(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert Story.objects.filter(site=site).count() == 1
        assert StoryPage.objects.all().count() == 2
        assert StoryPage.objects.filter(story=story).count() == 2
        assert StoryPage.objects.get(id=page1.id).ordering == 1
        assert StoryPage.objects.get(id=page2.id).ordering == 0

        assert response_data["pages"][0]["text"] == page2.text
        assert response_data["pages"][1]["text"] == page1.text

    @pytest.mark.django_db
    def test_partial_update_page_order(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(visibility=Visibility.PUBLIC, site=site)

        page1 = factories.StoryPageFactory.create(
            visibility=Visibility.PUBLIC, story=story, ordering=0
        )
        page2 = factories.StoryPageFactory.create(
            visibility=Visibility.PUBLIC, story=story, ordering=1
        )

        assert Story.objects.filter(site=site).count() == 1
        assert StoryPage.objects.all().count() == 2
        assert StoryPage.objects.filter(story=story).count() == 2
        assert StoryPage.objects.get(id=page1.id).ordering == 0
        assert StoryPage.objects.get(id=page2.id).ordering == 1

        response = self.client.get(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["pages"][0]["text"] == page1.text
        assert response_data["pages"][1]["text"] == page2.text

        data = {"pages": [str(page2.id), str(page1.id)]}

        response = self.client.patch(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug),
            data=json.dumps(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert Story.objects.filter(site=site).count() == 1
        assert StoryPage.objects.all().count() == 2
        assert StoryPage.objects.filter(story=story).count() == 2
        assert StoryPage.objects.get(id=page1.id).ordering == 1
        assert StoryPage.objects.get(id=page2.id).ordering == 0

        assert response_data["pages"][0]["text"] == page2.text
        assert response_data["pages"][1]["text"] == page1.text

    @pytest.mark.django_db
    def test_update_page_order_no_orphans(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(visibility=Visibility.PUBLIC, site=site)

        page1 = factories.StoryPageFactory.create(
            visibility=Visibility.PUBLIC, story=story, ordering=0
        )
        page2 = factories.StoryPageFactory.create(
            visibility=Visibility.PUBLIC, story=story, ordering=1
        )

        assert Story.objects.filter(site=site).count() == 1
        assert StoryPage.objects.all().count() == 2
        assert StoryPage.objects.filter(story=story).count() == 2
        assert StoryPage.objects.get(id=page1.id).ordering == 0
        assert StoryPage.objects.get(id=page2.id).ordering == 1

        response = self.client.get(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["pages"][0]["text"] == page1.text
        assert response_data["pages"][1]["text"] == page2.text

        data = {"pages": [str(page2.id)]}

        response = self.client.patch(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug),
            data=json.dumps(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert Story.objects.filter(site=site).count() == 1
        assert StoryPage.objects.all().count() == 1
        assert StoryPage.objects.filter(story=story).count() == 1
        assert StoryPage.objects.get(id=page2.id).ordering == 0

        assert response_data["pages"][0]["text"] == page2.text
