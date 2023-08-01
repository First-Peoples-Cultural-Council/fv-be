import json

import pytest

from backend.models.constants import Role, Visibility
from backend.models.story import Story
from backend.tests import factories

from .base_api_test import (
    BaseControlledSiteContentApiTest,
    SiteContentPatchApiTestMixin,
)
from .base_media_test import RelatedMediaTestMixin


class TestStoryEndpoint(
    RelatedMediaTestMixin,
    SiteContentPatchApiTestMixin,
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
        cover_image = factories.ImageFactory.create(site=site)

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
            "coverImage": str(cover_image.id),
            "visibility": "Public",
            "title": "Title",
            "titleTranslation": "A translation of the title",
            "introduction": "introduction",
            "introductionTranslation": "A translation of the introduction",
            "notes": ["Test Note One", "Test Note Two", "Test Note Three"],
            "acknowledgements": ["Test Author", "Another Acknowledgement"],
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
        assert actual_instance.notes[0] == expected_data["notes"][0]
        assert (
            actual_instance.acknowledgements[0] == expected_data["acknowledgements"][0]
        )
        assert str(actual_instance.cover_image.id) == expected_data["coverImage"]

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

        assert actual_response["coverImage"]["id"] == expected_data["coverImage"]
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

    def get_expected_list_response_item(self, story, site):
        return {
            "url": f"http://testserver{self.get_detail_endpoint(key=story.id, site_slug=site.slug)}",
            "id": str(story.id),
            "visibility": "Public",
            "title": story.title,
            "coverImage": None,
            "titleTranslation": story.title_translation,
            "excludeFromGames": False,
            "excludeFromKids": False,
            "hideOverlay": story.hide_overlay,
        }

    def get_expected_response(self, story, site):
        return {
            "created": story.created.astimezone().isoformat(),
            "lastModified": story.last_modified.astimezone().isoformat(),
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
            "url": f"http://testserver{self.get_detail_endpoint(key=story.id, site_slug=site.slug)}",
            "id": str(story.id),
            "visibility": "Public",
            "title": story.title,
            "site": {
                "id": str(site.id),
                "title": site.title,
                "slug": site.slug,
                "url": f"http://testserver/api/1.0/sites/{site.slug}",
                "language": site.language.title,
                "visibility": "Public",
            },
            "coverImage": None,
            "titleTranslation": story.title_translation,
            "introduction": story.introduction,
            "introductionTranslation": story.introduction_translation,
            "notes": [],
            "pages": [],
            "acknowledgements": [],
            "excludeFromGames": story.exclude_from_games,
            "excludeFromKids": story.exclude_from_kids,
            "author": story.author,
            "hideOverlay": story.hide_overlay,
        }

    def create_original_instance_for_patch(self, site):
        audio = factories.AudioFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)
        cover_image = factories.ImageFactory.create(site=site)
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
            cover_image=cover_image,
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
        assert updated_instance.cover_image == original_instance.cover_image
        assert (
            updated_instance.exclude_from_games == original_instance.exclude_from_games
        )
        assert updated_instance.exclude_from_kids == original_instance.exclude_from_kids
        assert updated_instance.related_audio == original_instance.related_audio
        assert updated_instance.related_images == original_instance.related_images
        assert updated_instance.related_videos == original_instance.related_videos
        assert updated_instance.pages.first() == original_instance.pages.first()

    def assert_patch_instance_updated_fields(self, data, updated_instance: Story):
        assert updated_instance.title == data["title"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["title"] == data["title"]
        assert actual_response["relatedAudio"][0]["id"] == str(
            original_instance.related_audio.first().id
        )
        assert actual_response["relatedImages"][0]["id"] == str(
            original_instance.related_images.first().id
        )
        assert actual_response["relatedVideos"][0]["id"] == str(
            original_instance.related_videos.first().id
        )
        assert actual_response["hideOverlay"] == original_instance.hide_overlay
        assert actual_response["coverImage"]["id"] == str(
            original_instance.cover_image.id
        )
        assert (
            actual_response["visibility"] == original_instance.get_visibility_display()
        )
        assert (
            actual_response["titleTranslation"] == original_instance.title_translation
        )
        assert actual_response["introduction"] == original_instance.introduction
        assert (
            actual_response["introductionTranslation"]
            == original_instance.introduction_translation
        )
        assert actual_response["notes"][0] == original_instance.notes[0]
        assert (
            actual_response["pages"][0]["text"] == original_instance.pages.first().text
        )
        assert (
            actual_response["acknowledgements"][0]
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
