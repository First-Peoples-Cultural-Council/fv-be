import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from ...models import Page, Story
from .base_api_test import BaseControlledSiteContentApiTest
from .base_media_test import RelatedMediaTestMixin


class TestStoryEndpoint(RelatedMediaTestMixin, BaseControlledSiteContentApiTest):
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

        generated_media = {}
        for purpose in ("story", "page1", "page2"):
            images = []
            videos = []
            audio = []
            for _unused in range(3):
                generated_media[purpose] = {}

                images.append(factories.ImageFactory.create(site=site))
                videos.append(factories.VideoFactory.create(site=site))
                audio.append(factories.AudioFactory.create(site=site))

                generated_media[purpose] = {
                    "related_images": images,
                    "related_videos": videos,
                    "related_audio": audio,
                }

        return {
            "relatedAudio": list(
                map(lambda x: str(x.id), generated_media["story"]["related_audio"])
            ),
            "relatedImages": list(
                map(lambda x: str(x.id), generated_media["story"]["related_images"])
            ),
            "relatedVideos": list(
                map(lambda x: str(x.id), generated_media["story"]["related_videos"])
            ),
            "coverImage": str(cover_image.id),
            "visibility": "Public",
            "title": "Title",
            "titleTranslation": "A translation of the title",
            "introduction": "introduction",
            "introductionTranslation": "A translation of the introduction",
            "notes": ["Test Note One", "Test Note Two", "Test Note Three"],
            "pages": [
                {
                    "text": "First text page",
                    "translation": "Translated 1st",
                    "relatedAudio": list(
                        map(
                            lambda x: str(x.id),
                            generated_media["page1"]["related_audio"],
                        )
                    ),
                    "relatedImages": list(
                        map(
                            lambda x: str(x.id),
                            generated_media["page1"]["related_images"],
                        )
                    ),
                    "relatedVideos": list(
                        map(
                            lambda x: str(x.id),
                            generated_media["page1"]["related_videos"],
                        )
                    ),
                },
                {
                    "text": "Second text page",
                    "translation": "Translated 2nd",
                    "relatedAudio": list(
                        map(
                            lambda x: str(x.id),
                            generated_media["page2"]["related_audio"],
                        )
                    ),
                    "relatedImages": list(
                        map(
                            lambda x: str(x.id),
                            generated_media["page2"]["related_images"],
                        )
                    ),
                    "relatedVideos": list(
                        map(
                            lambda x: str(x.id),
                            generated_media["page2"]["related_videos"],
                        )
                    ),
                },
            ],
            "acknowledgements": ["Test Authour", "Another Acknowledgement"],
            "excludeFromGames": True,
            "excludeFromKids": False,
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

        actual_pages = Page.objects.filter(story__id=actual_instance.id)

        assert len(actual_pages) == len(expected_data["pages"])

        for index, page in enumerate(expected_data["pages"]):
            assert page["text"] == actual_pages[index].text
            assert page["translation"] == actual_pages[index].translation
            assert len(page["relatedVideos"]) == 3

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["pages"][0]["text"] == expected_data["pages"][0]["text"]
        assert len(actual_response["pages"][0]["relatedAudio"]) == 3

        response_related_audio_ids = []
        for i in actual_response["relatedAudio"]:
            response_related_audio_ids.append(i["id"])

        response_related_image_ids = []
        for i in actual_response["relatedImages"]:
            response_related_image_ids.append(i["id"])

        response_related_video_ids = []
        for i in actual_response["relatedVideos"]:
            response_related_video_ids.append(i["id"])

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

    def assert_created_instance(self, pk, data):
        instance = Story.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def add_related_objects(self, instance):
        factories.PagesFactory.create(story=instance)
        factories.PagesFactory.create(story=instance)

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
            "excludeFromGames": False,
            "excludeFromKids": False,
        }

    @pytest.mark.django_db
    def test_pages_order(self):
        """Verify pages come back in defined order"""

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(visibility=Visibility.TEAM, site=site)

        page1 = factories.PagesFactory.create(story=story, ordering=10)
        page2 = factories.PagesFactory.create(story=story, ordering=20)

        response = self.client.get(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["pages"][0]["text"] == page1.text
        assert response_data["pages"][1]["text"] == page2.text
