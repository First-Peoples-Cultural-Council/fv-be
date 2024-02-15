import pytest

from backend.models.constants import Role, Visibility
from backend.models.galleries import Gallery, GalleryItem
from backend.tests import factories

from .base_api_test import BaseUncontrolledSiteContentApiTest
from .base_media_test import MediaTestMixin


class TestGalleryEndpoints(MediaTestMixin, BaseUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the gallery API endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:gallery-list"
    API_DETAIL_VIEW = "api:gallery-detail"

    model = Gallery

    def create_minimal_instance(self, site, visibility):
        gallery = factories.GalleryFactory(site=site, cover_image=None)
        return gallery

    def get_expected_response(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        return {
            **standard_fields,
            "titleTranslation": instance.title_translation,
            "introduction": instance.introduction,
            "introductionTranslation": instance.introduction_translation,
            "coverImage": None,
        }

    def get_expected_gallery_item_data(self, item):
        data = self.get_expected_image_data(item.image)
        data["ordering"] = item.ordering
        return data

    def get_expected_detail_response(self, instance, site):
        expected_response = self.get_expected_response(instance, site)
        expected_response["galleryItems"] = [
            self.get_expected_gallery_item_data(item)
            for item in instance.galleryitem_set.all()
        ]
        return expected_response

    def get_valid_data(self, site=None):
        image = factories.ImageFactory.create(site=site)
        image2 = factories.ImageFactory.create(site=site)
        return {
            "title": "Test Gallery",
            "titleTranslation": "Test Gallery Translation",
            "introduction": "Test Gallery Introduction",
            "introductionTranslation": "Test Gallery Introduction Translation",
            "coverImage": None,
            "galleryItems": [str(image.id), str(image2.id)],
        }

    def get_valid_patch_data(self, site=None):
        return {
            "title": "Updated Gallery",
        }

    def add_expected_defaults(self, data):
        return {
            **data,
            "titleTranslation": "",
            "introduction": "",
            "introductionTranslation": "",
            "coverImage": None,
            "galleryItems": [],
        }

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.title_translation == expected_data["titleTranslation"]
        assert actual_instance.introduction == expected_data["introduction"]
        assert (
            actual_instance.introduction_translation
            == expected_data["introductionTranslation"]
        )
        assert actual_instance.cover_image == expected_data["coverImage"]

        gallery_items = GalleryItem.objects.filter(gallery=actual_instance)
        assert len(gallery_items) == len(expected_data["galleryItems"])

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["titleTranslation"] == expected_data["titleTranslation"]
        assert actual_response["introduction"] == expected_data["introduction"]
        assert (
            actual_response["introductionTranslation"]
            == expected_data["introductionTranslation"]
        )
        assert actual_response["coverImage"] == expected_data["coverImage"]

        gallery_items = actual_response["galleryItems"]
        assert len(gallery_items) == len(expected_data["galleryItems"])

    def assert_created_instance(self, pk, data):
        instance = Gallery.objects.get(pk=pk)
        self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def add_related_objects(self, instance):
        image = factories.ImageFactory.create(site=instance.site)
        factories.GalleryItemFactory.create(gallery=instance, image=image)

    def assert_related_objects_deleted(self, instance):
        assert not GalleryItem.objects.filter(gallery=instance).exists()

    def create_original_instance_for_patch(self, site):
        return self.create_minimal_instance(site, Visibility.PUBLIC)

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.title_translation == original_instance.title_translation
        assert updated_instance.introduction == original_instance.introduction
        assert (
            updated_instance.introduction_translation
            == original_instance.introduction_translation
        )
        assert updated_instance.cover_image == original_instance.cover_image
        assert (
            updated_instance.galleryitem_set.count()
            == original_instance.galleryitem_set.count()
        )

    def assert_patch_instance_updated_fields(self, data, updated_instance):
        assert updated_instance.title == data["title"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["title"] == data["title"]
        assert (
            actual_response["titleTranslation"] == original_instance.title_translation
        )
        assert actual_response["introduction"] == original_instance.introduction
        assert (
            actual_response["introductionTranslation"]
            == original_instance.introduction_translation
        )
        assert actual_response["coverImage"] == original_instance.cover_image
        assert (
            len(actual_response["galleryItems"])
            == original_instance.galleryitem_set.count()
        )

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": "Test Gallery",
        }

    @pytest.mark.django_db
    def test_gallery_cover_image_not_unique(self):
        """Galleries can be created using the same image as their cover image"""
        site, user = factories.access.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        image = factories.ImageFactory.create(site=site)
        data = self.get_valid_data(site=site)
        data["coverImage"] = str(image.id)

        self.client.force_authenticate(user=user)
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201

        data["title"] = "Test Gallery 2"
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 201
        assert Gallery.objects.filter(cover_image=image).count() == 2

    @pytest.mark.django_db
    def test_gallery_duplicate_image_400_error(self):
        """Galleries cannot be created using the same image multiple times"""
        site, user = factories.access.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        image = factories.ImageFactory.create(site=site)
        data = self.get_valid_data(site=site)
        data["galleryItems"] = [str(image.id), str(image.id)]

        self.client.force_authenticate(user=user)
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )

        assert response.status_code == 400

    @pytest.mark.django_db
    def test_gallery_always_ordered_by_input(self):
        """Galleries are always ordered in the same order as the ids in the request"""
        site, user = factories.access.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        image = factories.ImageFactory.create(site=site)
        image2 = factories.ImageFactory.create(site=site)
        image3 = factories.ImageFactory.create(site=site)
        data = self.get_valid_data(site=site)
        data["galleryItems"] = [str(image2.id), str(image.id), str(image3.id)]

        self.client.force_authenticate(user=user)
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )
        response_data = response.json()

        assert response.status_code == 201
        assert response_data["galleryItems"][0]["id"] == str(image2.id)
        assert response_data["galleryItems"][0]["ordering"] == 0
        assert response_data["galleryItems"][1]["id"] == str(image.id)
        assert response_data["galleryItems"][1]["ordering"] == 1
        assert response_data["galleryItems"][2]["id"] == str(image3.id)
        assert response_data["galleryItems"][2]["ordering"] == 2

        gallery = Gallery.objects.get(id=response_data["id"])
        assert gallery.galleryitem_set.filter(image=image2).first().ordering == 0
        assert gallery.galleryitem_set.filter(image=image).first().ordering == 1
        assert gallery.galleryitem_set.filter(image=image3).first().ordering == 2
