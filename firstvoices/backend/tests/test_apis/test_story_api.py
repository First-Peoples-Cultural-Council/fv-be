import json

import pytest

from backend.models.constants import Role, Visibility
from backend.models.story import Story, StoryPage
from backend.tests import factories
from backend.tests.test_apis.base.base_api_test import BaseControlledSiteContentApiTest
from backend.tests.test_apis.base.base_media_test import RelatedMediaTestMixin


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
    model_factory = factories.StoryFactory

    def create_minimal_instance(self, site, visibility):
        return factories.StoryFactory.create(site=site, visibility=visibility)

    def get_valid_data(self, site=None):
        related_media = self.get_valid_related_media_data(site=site)

        return {
            **related_media,
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

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": "Title",
            "visibility": "Public",
            "pages": [],
        }

    def get_valid_data_with_null_optional_charfields(self, site=None):
        return {
            "title": "Title",
            "visibility": "Public",
            "pages": [],
            "titleTranslation": None,
            "introduction": None,
            "introductionTranslation": None,
            "author": None,
        }

    def get_valid_page_data(self, site, story, page):
        return {
            "id": str(page.id),
            "url": f"http://testserver{self.get_detail_endpoint(key=story.id, site_slug=site.slug)}/pages/{page.id}",
            "text": page.text,
            "translation": page.translation,
            "notes": page.notes,
            "ordering": page.ordering,
            "relatedAudio": list(page.related_audio.all()),
            "relatedDocuments": list(page.related_documents.all()),
            "relatedImages": list(page.related_images.all()),
            "relatedVideos": list(page.related_videos.all()),
            "relatedVideoLinks": page.related_video_links,
        }

    def add_expected_defaults(self, data):
        return {
            **data,
            "author": "",
            "hideOverlay": False,
            "titleTranslation": "",
            "introduction": "",
            "introductionTranslation": "",
            "notes": [],
            "acknowledgements": [],
            "excludeFromGames": False,
            "excludeFromKids": False,
            **self.RELATED_MEDIA_DEFAULTS,
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

        assert len(expected_data["notes"]) == len(actual_instance.notes)
        for i, n in enumerate(expected_data["notes"]):
            assert actual_instance.notes[i] == n["text"]

        assert len(expected_data["acknowledgements"]) == len(
            actual_instance.acknowledgements
        )
        for i, ack in enumerate(expected_data["acknowledgements"]):
            assert actual_instance.acknowledgements[i] == ack["text"]

        self.assert_updated_instance_related_media(expected_data, actual_instance)

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]

        self.assert_update_response_related_media(expected_data, actual_response)

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
            **self.RELATED_MEDIA_DEFAULTS,
        }

    def create_original_instance_for_patch(self, site):
        related_media = self.get_related_media_for_patch(site=site)
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
            **related_media,
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

        assert (
            updated_instance.related_video_links
            == original_instance.related_video_links
        )

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
            **self.RELATED_MEDIA_DEFAULTS,
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
    def test_update_page_missing_page_id(self):
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
        assert Story.objects.get(id=story.id).pages.count() == 2

        data = {"pages": [str(page2.id)]}

        response = self.client.patch(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug),
            data=json.dumps(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            response_data[0]
            == f"Existing story page with ID {page1.id} is missing from the updated list."
        )

        assert Story.objects.filter(site=site).count() == 1
        assert StoryPage.objects.all().count() == 2
        assert StoryPage.objects.filter(story=story).count() == 2
        assert StoryPage.objects.get(id=page1.id).ordering == 0
        assert StoryPage.objects.get(id=page2.id).ordering == 1
        assert Story.objects.get(id=story.id).pages.count() == 2

    @pytest.mark.django_db
    def test_update_page_order_wrong_story(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        story_one = factories.StoryFactory.create(
            visibility=Visibility.PUBLIC, site=site
        )
        story_two = factories.StoryFactory.create(
            visibility=Visibility.PUBLIC, site=site
        )

        page1 = factories.StoryPageFactory.create(
            visibility=Visibility.PUBLIC, story=story_one, ordering=0
        )
        page2 = factories.StoryPageFactory.create(
            visibility=Visibility.PUBLIC, story=story_two, ordering=1
        )

        assert Story.objects.filter(site=site).count() == 2
        assert StoryPage.objects.all().count() == 2
        assert StoryPage.objects.filter(story=story_one).count() == 1
        assert StoryPage.objects.get(id=page1.id).ordering == 0
        assert StoryPage.objects.get(id=page1.id).story == story_one

        data = {"pages": [str(page2.id), str(page1.id)]}

        response = self.client.patch(
            self.get_detail_endpoint(key=story_one.id, site_slug=site.slug),
            data=json.dumps(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)

        assert (
            response_data[0] == f"Page with ID {page2.id} does not belong to the story."
        )
        assert Story.objects.filter(site=site).count() == 2
        assert StoryPage.objects.all().count() == 2
        assert StoryPage.objects.filter(story=story_one).count() == 1
        assert StoryPage.objects.get(id=page1.id).ordering == 0
        assert StoryPage.objects.get(id=page1.id).story == story_one

    @pytest.mark.django_db
    def test_detail_parameter(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(
            user=user, site=site, role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        story = factories.StoryFactory.create(visibility=Visibility.PUBLIC, site=site)
        page = factories.StoryPageFactory.create(
            visibility=Visibility.PUBLIC, story=story, ordering=0
        )

        response = self.client.get(
            self.get_list_endpoint(site_slug=site.slug, query_kwargs={"detail": "True"})
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        result = response_data["results"][0]

        assert result["id"] == str(story.id)
        assert len(result["pages"]) == 1
        assert result["pages"][0] == self.get_valid_page_data(site, story, page)

    @pytest.mark.django_db
    def test_story_detail_page_related_media_ordered_by_created(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        story = factories.StoryFactory.create(site=site, visibility=Visibility.PUBLIC)
        page = factories.StoryPageFactory.create(site=site, story=story, ordering=1)
        audio1 = factories.AudioFactory.create(site=site)
        audio2 = factories.AudioFactory.create(site=site)
        image1 = factories.ImageFactory.create(site=site)
        image2 = factories.ImageFactory.create(site=site)
        video1 = factories.VideoFactory.create(site=site)
        video2 = factories.VideoFactory.create(site=site)

        page.related_audio.add(audio2)
        page.related_audio.add(audio1)

        page.related_images.add(image2)
        page.related_images.add(image1)

        page.related_videos.add(video2)
        page.related_videos.add(video1)

        response = self.client.get(
            self.get_detail_endpoint(key=story.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["pages"][0]["relatedAudio"][0]["id"] == str(audio1.id)
        assert response_data["pages"][0]["relatedAudio"][1]["id"] == str(audio2.id)
        assert response_data["pages"][0]["relatedImages"][0]["id"] == str(image1.id)
        assert response_data["pages"][0]["relatedImages"][1]["id"] == str(image2.id)
        assert response_data["pages"][0]["relatedVideos"][0]["id"] == str(video1.id)
        assert response_data["pages"][0]["relatedVideos"][1]["id"] == str(video2.id)
