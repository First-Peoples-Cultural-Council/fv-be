import json

import pytest
from django.test.client import encode_multipart
from rest_framework.reverse import reverse

from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.factories import (
    get_site_with_anonymous_user,
    get_site_with_authenticated_member,
    get_site_with_authenticated_nonmember,
    get_site_with_staff_user,
)
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseUncontrolledSiteContentApiTest,
)
from backend.tests.utils import get_sample_file

VIMEO_VIDEO_LINK = "https://vimeo.com/226053498"
YOUTUBE_VIDEO_LINK = "https://www.youtube.com/watch?v=N_Iyb0LkDUc"
MOCK_EMBED_LINK = "https://mock_embed_link.com/"
MOCK_THUMBNAIL_LINK = "https://mock_thumbnail_link.com/"


class FormDataMixin:
    content_type = "multipart/form-data; boundary=TestBoundaryString"
    boundary_string = "TestBoundaryString"

    def format_upload_data(self, data):
        """Encode multipart form data instead of json"""
        return encode_multipart(self.boundary_string, data)


class MediaTestMixin:
    """
    Utilities for testing media APIs
    """

    def get_basic_media_data(self, instance, view_name):
        url = reverse(
            view_name, current_app=self.APP_NAME, args=[instance.site.slug, instance.id]
        )

        data = {
            "id": str(instance.id),
            "url": f"http://testserver{url}",
            "title": instance.title,
            "description": instance.description,
            "acknowledgement": instance.acknowledgement,
            "excludeFromGames": instance.exclude_from_games,
            "excludeFromKids": instance.exclude_from_kids,
        }
        return data

    def get_usage_data(self):
        return {
            "characters": [],
            "dictionaryEntries": [],
            "songs": [],
            "stories": [],
            "total": 0,
        }

    def get_video_usage_data(self):
        usage = {
            **self.get_usage_data(),
            "customPages": [],
        }

        return usage

    def get_image_usage_data(self):
        usage = {
            **self.get_video_usage_data(),
            "gallery": [],
            "siteBanner": {},
            "siteLogo": {},
        }

        return usage

    def get_file_data(self, file):
        return {
            "path": f"http://testserver{file.content.url}",
            "mimetype": file.mimetype,
            "size": file.size,
        }

    def get_visual_file_data(self, file):
        if file:
            return {
                **self.get_file_data(file),
                "height": file.height,
                "width": file.width,
            }
        else:
            return None

    def get_media_thumbnail_data(self, instance):
        return {
            "thumbnail": self.get_visual_file_data(instance.thumbnail),
            "small": self.get_visual_file_data(instance.small),
            "medium": self.get_visual_file_data(instance.medium),
        }

    def get_visual_media_data(self, instance, view_name):
        data = self.get_basic_media_data(instance, view_name=view_name)
        thumbnail_data = self.get_media_thumbnail_data(instance)

        data = {
            **data,
            **thumbnail_data,
            "original": self.get_visual_file_data(instance.original),
        }

        return data

    def get_expected_image_data(self, instance, detail_view=False):
        data = self.get_visual_media_data(instance, view_name="api:image-detail")

        if detail_view:
            data["usage"] = self.get_image_usage_data()

        return data

    def get_expected_video_data(self, instance, detail_view=False):
        data = self.get_visual_media_data(instance, view_name="api:video-detail")

        if detail_view:
            data["usage"] = self.get_video_usage_data()

        return data

    def get_expected_audio_data(self, instance, speaker, detail_view=False):
        data = self.get_basic_media_data(instance, view_name="api:audio-detail")
        data["original"] = self.get_file_data(instance.original)

        if detail_view:
            data["usage"] = self.get_usage_data()

        if speaker:
            speaker_url = reverse(
                "api:person-detail",
                current_app=self.APP_NAME,
                args=[speaker.site.slug, speaker.id],
            )

            data["speakers"] = [
                {
                    "url": f"http://testserver{speaker_url}",
                    "id": str(speaker.id),
                    "name": speaker.name,
                    "bio": speaker.bio,
                }
            ]
        else:
            data["speakers"] = []

        return data

    def get_expected_document_data(self, instance, detail_view=False):
        data = self.get_basic_media_data(instance, view_name="api:document-detail")
        data["original"] = self.get_file_data(instance.original)

        if detail_view:
            data["usage"] = self.get_usage_data()

        return data


class RelatedMediaTestMixin(MediaTestMixin):
    """
    For APIs that use the RelatedMediaSerializerMixin.
    """

    RELATED_MEDIA_DEFAULTS = {
        "relatedAudio": [],
        "relatedDocuments": [],
        "relatedImages": [],
        "relatedVideos": [],
        "relatedVideoLinks": [],
    }

    model = None
    model_factory = None

    def create_instance_with_media(
        self,
        site,
        visibility,
        related_audio=None,
        related_documents=None,
        related_images=None,
        related_videos=None,
        related_video_links=None,
    ):
        if related_video_links is None:
            related_video_links = []
        return self.model_factory.create(
            site=site,
            visibility=visibility,
            related_audio=related_audio,
            related_documents=related_documents,
            related_images=related_images,
            related_videos=related_videos,
            related_video_links=related_video_links,
        )

    def get_valid_related_media_data(self, site=None):
        audio = factories.AudioFactory.create(site=site)
        document = factories.DocumentFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)

        return {
            "relatedAudio": [str(audio.id)],
            "relatedDocuments": [str(document.id)],
            "relatedImages": [str(image.id)],
            "relatedVideos": [str(video.id)],
            "relatedVideoLinks": [],
        }

    def get_related_media_for_patch(self, site=None):
        audio = factories.AudioFactory.create(site=site)
        document = factories.DocumentFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)

        return {
            "related_audio": (audio,),
            "related_documents": (document,),
            "related_images": (image,),
            "related_videos": (video,),
            "related_video_links": [YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK],
        }

    def assert_patch_instance_original_fields_related_media(
        self, original_instance, updated_instance
    ):
        assert updated_instance.related_audio == original_instance.related_audio
        assert updated_instance.related_documents == original_instance.related_documents
        assert updated_instance.related_images == original_instance.related_images
        assert updated_instance.related_videos == original_instance.related_videos
        assert (
            updated_instance.related_video_links
            == original_instance.related_video_links
        )

    def assert_update_patch_response_related_media(
        self, original_instance, actual_response
    ):
        assert actual_response["relatedAudio"][0]["id"] == str(
            original_instance.related_audio.first().id
        )
        assert actual_response["relatedDocuments"][0]["id"] == str(
            original_instance.related_documents.first().id
        )
        assert actual_response["relatedImages"][0]["id"] == str(
            original_instance.related_images.first().id
        )
        assert actual_response["relatedVideos"][0]["id"] == str(
            original_instance.related_videos.first().id
        )
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

    def assert_update_response_related_media(self, expected_data, actual_response):
        assert len(actual_response["relatedAudio"]) == len(
            expected_data["relatedAudio"]
        )
        for i, item in enumerate(expected_data["relatedAudio"]):
            assert actual_response["relatedAudio"][i]["id"] == item

        assert len(actual_response["relatedDocuments"]) == len(
            expected_data["relatedDocuments"]
        )
        for i, item in enumerate(expected_data["relatedDocuments"]):
            assert actual_response["relatedDocuments"][i]["id"] == item

        assert len(actual_response["relatedImages"]) == len(
            expected_data["relatedImages"]
        )
        for i, item in enumerate(expected_data["relatedImages"]):
            assert actual_response["relatedImages"][i]["id"] == item

        assert len(actual_response["relatedVideos"]) == len(
            expected_data["relatedVideos"]
        )
        for i, item in enumerate(expected_data["relatedVideos"]):
            assert actual_response["relatedVideos"][i]["id"] == item

        assert (
            actual_response["relatedVideoLinks"] == expected_data["relatedVideoLinks"]
        )

    def assert_updated_instance_related_media(self, expected_data, actual_instance):
        assert len(actual_instance.related_audio.all()) == len(
            expected_data["relatedAudio"]
        )
        for i, item in enumerate(expected_data["relatedAudio"]):
            assert str(actual_instance.related_audio.all()[i].id) == item

        assert len(actual_instance.related_documents.all()) == len(
            expected_data["relatedDocuments"]
        )
        for i, item in enumerate(expected_data["relatedDocuments"]):
            assert str(actual_instance.related_documents.all()[i].id) == item

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

    @pytest.mark.django_db
    def test_detail_related_audio_with_speaker(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        speaker = factories.PersonFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        factories.AudioSpeakerFactory.create(speaker=speaker, audio=audio)

        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_audio=(audio,)
        )

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["relatedAudio"]) == 1
        assert response_data["relatedAudio"][0] == self.get_expected_audio_data(
            audio, speaker, detail_view=False
        )

    @pytest.mark.django_db
    def test_detail_related_images(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        image = factories.ImageFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_images=(image,)
        )
        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["relatedImages"]) == 1

        expected = self.get_expected_image_data(image, detail_view=False)
        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in response_data["relatedImages"][0]:
                response_data["relatedImages"][0].pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert response_data["relatedImages"][0] == expected

    @pytest.mark.django_db
    def test_detail_related_videos(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        video = factories.VideoFactory.create(site=site)
        instance = self.create_instance_with_media(
            site=site, visibility=Visibility.PUBLIC, related_videos=(video,)
        )
        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["relatedVideos"]) == 1

        expected = self.get_expected_video_data(video, detail_view=False)
        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in response_data["relatedVideos"][0]:
                response_data["relatedVideos"][0].pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert response_data["relatedVideos"][0] == expected

    @pytest.mark.parametrize(
        "related_video_links, expected_response_codes",
        [
            ([YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK], [200, 201]),
            (
                [
                    "https://www.youtube.com/watch?v=abc1",
                    "https://www.youtube.com/watch?v=abc2",
                ],
                [200, 201],
            ),
            (
                [
                    YOUTUBE_VIDEO_LINK,
                    VIMEO_VIDEO_LINK,
                    VIMEO_VIDEO_LINK,
                ],
                [400],
            ),
            (
                [
                    "https://www.youtube.com/watch?v=abc",
                    "https://www.youtube.com/watch?v=abc",
                ],
                [400],
            ),
        ],
    )
    @pytest.mark.django_db
    def test_update_duplicate_related_video_links(
        self, related_video_links, expected_response_codes
    ):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )

        instance = self.create_instance_with_media(
            site=site,
            visibility=Visibility.TEAM,
            related_video_links=[],
        )

        req_body = {"related_video_links": related_video_links}

        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )
        assert response.status_code in expected_response_codes

    @pytest.mark.django_db
    def test_update_remove_related_video_links(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.TEAM, user_role=Role.LANGUAGE_ADMIN
        )

        instance = self.create_instance_with_media(
            site=site,
            visibility=Visibility.TEAM,
            related_video_links=[YOUTUBE_VIDEO_LINK, VIMEO_VIDEO_LINK],
        )

        req_body = {"related_video_links": []}

        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug),
            format="json",
            data=req_body,
        )
        response_data = json.loads(response.content)

        assert response.status_code in [200, 201]
        assert response_data["relatedVideoLinks"] == []


class BaseMediaApiTest(
    MediaTestMixin,
    FormDataMixin,
    BaseUncontrolledSiteContentApiTest,
):
    """
    Tests for the list, detail, create, and delete APIs for media endpoints.
    """

    sample_filename = "sample-image.jpg"
    sample_filetype = "image/jpeg"
    model = None
    model_factory = None
    related_key = None

    def create_minimal_instance(self, site, visibility):
        return self.model_factory.create(site=site)

    def create_original_instance_for_patch(self, site):
        instance = self.model_factory.create(
            site=site,
            title="Original title",
            description="Original description",
            acknowledgement="Original acknowledgement",
            exclude_from_kids=True,
            exclude_from_games=True,
        )
        instance.save()
        return instance

    # Overriding methods to add in the detail_view parameter as that affects the response in case of media APIs
    def get_expected_detail_response(self, instance, site):
        return self.get_expected_response(instance, site, detail_view=True)

    def get_expected_list_response_item(self, instance, site):
        return self.get_expected_response(instance, site, detail_view=False)

    def get_valid_data(self, site=None):
        """Returns a valid data object suitable for create/update requests"""
        return {
            "title": "A title for the media",
            "description": "Description of the media",
            "acknowledgement": "An acknowledgement of the media",
            "excludeFromGames": True,
            "excludeFromKids": True,
            "original": get_sample_file(self.sample_filename, self.sample_filetype),
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": "A title for the media",
            "original": get_sample_file(self.sample_filename, self.sample_filetype),
        }

    def add_expected_defaults(self, data):
        return {
            **data,
            "description": "",
            "acknowledgement": "",
            "excludeFromGames": False,
            "excludeFromKids": False,
        }

    def get_invalid_patch_data(self):
        """Add some actually invalid data-- empty data doesn't work for multipart encoder"""
        return {
            "excludeFromKids": "not a boolean value",
        }

    def get_valid_patch_data(self, site):
        return {
            "title": "A new title",
        }

    def get_valid_patch_file_data(self, site):
        return {
            "original": get_sample_file(
                self.sample_filename,
                self.sample_filetype,
                f"patch-{self.sample_filename}",
            ),
        }

    def assert_created_instance(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        assert instance.title == data["title"]
        assert instance.description == data["description"]

        # Split the filename and extension from the file paths and check for each to avoid async tests appending
        # characters to the end of the filename when file path already exists.
        data_filename = data["original"].name.split(".")[0]
        data_file_extension = data["original"].name.split(".")[1]
        instance_filename = instance.original.content.name.split(".")[0]
        instance_file_extension = instance.original.content.name.split(".")[1]
        assert data_filename in instance_filename
        assert data_file_extension in instance_file_extension

        assert instance.acknowledgement == data["acknowledgement"]
        assert instance.exclude_from_games == data["excludeFromGames"]
        assert instance.exclude_from_kids == data["excludeFromKids"]

    def add_related_objects(self, instance):
        # related files are added as part of minimal instance; nothing extra to add here
        pass

    def assert_related_objects_deleted(self, instance):
        self.assert_instance_deleted(instance.original)

    def assert_secondary_fields(self, expected_data, updated_instance):
        assert updated_instance.description == expected_data["description"]
        assert updated_instance.acknowledgement == expected_data["acknowledgement"]
        assert updated_instance.exclude_from_kids == expected_data["excludeFromKids"]
        assert updated_instance.exclude_from_games == expected_data["excludeFromGames"]

    def assert_patch_instance_updated_fields(self, data, updated_instance):
        assert updated_instance.title == data["title"]

    def assert_response(self, original_instance, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["description"] == expected_data["description"]
        assert actual_response["acknowledgement"] == expected_data["acknowledgement"]
        assert actual_response["excludeFromKids"] == expected_data["excludeFromKids"]
        assert actual_response["excludeFromGames"] == expected_data["excludeFromGames"]

        # The original file should not be updated, as it's a read-only field
        expected_file_path = (
            original_instance.original.content.url
            if hasattr(original_instance.original, "content")
            else original_instance.original.name
        )
        expected_filename = expected_file_path.split(".")[0]
        expected_file_extension = expected_file_path.split(".")[1]
        actual_filename = actual_response["original"]["path"].split(".")[0]
        actual_file_extension = actual_response["original"]["path"].split(".")[1]
        assert expected_filename in actual_filename
        assert expected_file_extension in actual_file_extension

    def assert_update_response(self, expected_data, actual_response, instance):
        self.assert_response(
            actual_response=actual_response,
            expected_data={**expected_data},
            original_instance=instance,
        )

    @pytest.mark.django_db
    def test_update_success_200(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data(site)

        response_data = self.perform_successful_detail_request(instance, site, data)

        self.assert_update_response(data, response_data, instance)

    @pytest.mark.django_db
    def test_update_with_nulls_success_200(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data_with_nulls(site)
        expected_data = self.add_expected_defaults(data)

        response_data = self.perform_successful_detail_request(instance, site, data)

        self.assert_updated_instance(expected_data, self.get_updated_instance(instance))
        self.assert_update_response(expected_data, response_data, instance)

    def assert_update_patch_file_response(
        self, original_instance, data, actual_response
    ):
        expected_data = {
            "id": str(original_instance.id),
            "title": original_instance.title,
            "description": original_instance.description,
            "acknowledgement": original_instance.acknowledgement,
            "excludeFromKids": original_instance.exclude_from_kids,
            "excludeFromGames": original_instance.exclude_from_games,
            "original": data["original"],
        }

        self.assert_response(
            original_instance=original_instance,
            actual_response=actual_response,
            expected_data=expected_data,
        )

    @pytest.mark.django_db
    def test_create_400_invalid_filetype(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        data = self.get_valid_data(site)
        data["original"] = (get_sample_file("file.txt", self.sample_filetype),)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    def test_create_permissions_valid(self, role):
        site, _ = get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, role
        )
        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

    @pytest.mark.django_db
    def test_create_permissions_valid_superadmin(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)
        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "get_site_with_user",
        [
            get_site_with_authenticated_member,
            get_site_with_authenticated_nonmember,
            get_site_with_anonymous_user,
            get_site_with_staff_user,
        ],
    )
    def test_create_permissions_denied(self, get_site_with_user):
        site, _ = get_site_with_user(self.client)
        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    def test_update_permissions_valid(self, role):
        site, _ = get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, role
        )
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data(site)

        self.perform_successful_detail_request(instance, site, data)

    @pytest.mark.django_db
    def test_update_permissions_valid_superadmin(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data(site)

        self.perform_successful_detail_request(instance, site, data)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "get_site_with_user",
        [
            get_site_with_authenticated_member,
            get_site_with_authenticated_nonmember,
            get_site_with_anonymous_user,
            get_site_with_staff_user,
        ],
    )
    def test_update_permissions_denied(self, get_site_with_user):
        site, _ = get_site_with_user(self.client, Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        data = self.get_valid_data(site)

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )
        assert response.status_code == 403

    def get_media_instance_that_has_usages(self, site, visibility=Visibility.PUBLIC):
        """Create a media instance and add that instance to 5 separate entries
        Returns: media instance e.g. Video, Image, Audio, or Document
        """
        media_instance = self.create_minimal_instance(
            site, visibility=Visibility.PUBLIC
        )

        def add_media_instance_to(target):
            related_list = getattr(target, self.related_key)
            related_list.add(media_instance)

        character = factories.CharacterFactory(site=site, title="a", sort_order=1)
        add_media_instance_to(character)

        dict_entry = factories.DictionaryEntryFactory(site=site, visibility=visibility)
        add_media_instance_to(dict_entry)

        song = factories.SongFactory(site=site, visibility=visibility)
        add_media_instance_to(song)

        story_1 = factories.StoryFactory(site=site, visibility=visibility)
        story_1_page = factories.StoryPageFactory(
            site=site, story=story_1, visibility=visibility
        )
        add_media_instance_to(story_1)
        add_media_instance_to(story_1_page)

        story_2 = factories.StoryFactory(site=site, visibility=visibility)
        story_2_page = factories.StoryPageFactory(
            site=site, story=story_2, visibility=visibility
        )
        add_media_instance_to(story_2_page)

        return media_instance

    @pytest.mark.django_db
    def test_usages_field_base(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        media_instance = self.get_media_instance_that_has_usages(
            site, visibility=Visibility.PUBLIC
        )

        response = self.client.get(
            self.get_detail_endpoint(
                key=media_instance.id,
                site_slug=site.slug,
            )
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        # usage in characters
        character_usage = response_data["usage"]["characters"]
        assert len(character_usage) == 1
        assert character_usage[0]["id"] == str(media_instance.character_set.first().id)

        # usage in dictionary entries
        dict_entry_usage = response_data["usage"]["dictionaryEntries"]
        assert len(dict_entry_usage) == 1
        assert dict_entry_usage[0]["id"] == str(
            media_instance.dictionaryentry_set.first().id
        )

        # usage in songs
        song_usage = response_data["usage"]["songs"]
        assert len(song_usage) == 1
        assert song_usage[0]["id"] == str(media_instance.song_set.first().id)

        # usage in stories
        # Story pages point to the story, so the response here should only contain id's of both stories exactly once
        story_usage = response_data["usage"]["stories"]
        expected_stories_ids = set()

        for e in media_instance.story_set.all():
            expected_stories_ids.add(str(e.id))

        for e in media_instance.storypage_set.all():
            expected_stories_ids.add(str(e.story_id))

        assert len(story_usage) == len(expected_stories_ids)
        assert story_usage[0]["id"] in expected_stories_ids
        assert story_usage[1]["id"] in expected_stories_ids

        assert response_data["usage"]["total"] == 5

    @pytest.mark.django_db
    def test_usages_field_permissions(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        media_instance = self.get_media_instance_that_has_usages(
            site, visibility=Visibility.TEAM
        )

        response = self.client.get(
            self.get_detail_endpoint(
                key=media_instance.id,
                site_slug=site.slug,
            )
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)

        # Characters visibility depends on the site's visibility, PUBLIC in this case
        assert len(response_data["usage"]["characters"]) == 1

        # controlled content should be available
        assert len(response_data["usage"]["dictionaryEntries"]) == 0
        assert len(response_data["usage"]["songs"]) == 0
        assert len(response_data["usage"]["stories"]) == 0

    @pytest.mark.skip(
        reason="Multipart form data not supported for null string values."
    )
    def test_create_with_null_optional_charfields_success_201(self):
        # This test is skipped because the multipart form data encoder does not support null string values.
        pass

    @pytest.mark.skip(
        reason="Multipart form data not supported for null string values."
    )
    def test_update_with_null_optional_charfields_success_200(self):
        # This test is skipped because the multipart form data encoder does not support null string values.
        pass

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        self.assert_original_secondary_fields(original_instance, updated_instance)
        assert updated_instance.original.id == original_instance.original.id

    def assert_original_secondary_fields(self, original_instance, updated_instance):
        # everything but title
        self.assert_secondary_fields(
            expected_data={
                "description": original_instance.description,
                "acknowledgement": original_instance.acknowledgement,
                "excludeFromKids": original_instance.exclude_from_kids,
                "excludeFromGames": original_instance.exclude_from_games,
            },
            updated_instance=updated_instance,
        )

    def assert_update_patch_response(self, original_instance, data, actual_response):
        self.assert_response(
            original_instance=original_instance,
            actual_response=actual_response,
            expected_data={
                "id": str(original_instance.id),
                "title": data["title"],
                "description": original_instance.description,
                "acknowledgement": original_instance.acknowledgement,
                "excludeFromKids": original_instance.exclude_from_kids,
                "excludeFromGames": original_instance.exclude_from_games,
                "original": original_instance.original,
            },
        )

    def assert_updated_instance(self, expected_data, actual_instance):
        self.assert_secondary_fields(expected_data, actual_instance)
        assert actual_instance.title == expected_data["title"]


class BaseVisualMediaAPITest(BaseMediaApiTest):
    @pytest.fixture()
    def disable_celery(self, settings):
        # Sets the celery tasks to run synchronously for testing
        settings.CELERY_TASK_ALWAYS_EAGER = True

    @pytest.mark.django_db
    def test_patch_file_is_ignored(self):
        # PUT/PATCH requests updating the original file should be ignored,
        # i.e. there will be no validation error but the file will also not be updated.
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)
        instance = self.create_original_instance_for_patch(site=site)
        data = self.get_valid_patch_file_data(site)

        response = self.client.patch(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(instance.id)

        # Verifying the file does not change
        assert instance.original.content.name in response_data["original"]["path"]

    def assert_related_objects_deleted(self, instance):
        self.assert_instance_deleted(instance.original)
        self.assert_instance_deleted(instance.medium)
        self.assert_instance_deleted(instance.small)
        self.assert_instance_deleted(instance.thumbnail)
