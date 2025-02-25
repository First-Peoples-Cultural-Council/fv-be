import json

import pytest

from backend.models.constants import Visibility
from backend.models.media import Image
from backend.tests import factories

from .base_media_test import BaseVisualMediaAPITest


class TestImagesEndpoint(BaseVisualMediaAPITest):
    """
    End-to-end tests that the images endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:image-list"
    API_DETAIL_VIEW = "api:image-detail"
    sample_filename = "sample-image.jpg"
    sample_filetype = "image/jpg"
    model = Image
    model_factory = factories.ImageFactory
    related_key = "related_images"

    def get_expected_response(self, instance, site, detail_view=False):
        return self.get_expected_image_data(instance, detail_view)

    def assert_created_response(
        self, expected_data, actual_response, detail_view=False
    ):
        instance = Image.objects.get(pk=actual_response["id"])
        expected = self.get_expected_image_data(instance, detail_view)
        for ignored_field in ("thumbnail", "small", "medium"):
            if ignored_field in actual_response:
                actual_response.pop(ignored_field)
            if ignored_field in expected:
                expected.pop(ignored_field)

        assert actual_response == expected

    @pytest.mark.django_db
    def test_usages_field_extra_fields(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)
        media_instance = self.create_minimal_instance(
            site, visibility=Visibility.PUBLIC
        )

        custom_page = factories.SitePageFactory(site=site, banner_image=media_instance)

        # logo and banner
        site.logo = media_instance
        site.banner_image = media_instance
        site.save()

        # Gallery
        gallery = factories.GalleryFactory(site=site, cover_image=media_instance)
        factories.GalleryItemFactory(gallery=gallery, image=media_instance)

        gallery_2 = factories.GalleryFactory(site=site, cover_image=media_instance)

        response = self.client.get(
            self.get_detail_endpoint(
                key=media_instance.id,
                site_slug=site.slug,
            )
        )
        assert response.status_code == 200
        response_data = json.loads(response.content)

        # usage in custom pages
        custom_pages = response_data["usage"]["customPages"]
        assert len(custom_pages) == 1
        assert custom_pages[0]["id"] == str(custom_page.id)

        # usage in sites
        assert response_data["usage"]["siteBanner"]["id"] == str(site.id)
        assert response_data["usage"]["siteLogo"]["id"] == str(site.id)

        # usage in gallery
        # should only return unique galleries, and gallery items should point to parent gallery
        gallery_usage = response_data["usage"]["gallery"]
        assert len(gallery_usage) == 2
        assert gallery_usage[0]["id"] == str(gallery.id)
        assert gallery_usage[1]["id"] == str(gallery_2.id)

        assert response_data["usage"]["total"] == 5
