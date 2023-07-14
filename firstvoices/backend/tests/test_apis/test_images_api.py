from backend.tests import factories

from .base_api_test import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    SiteContentDestroyApiTestMixin,
    WriteApiTestMixin,
)
from .base_media_test import FormDataMixin, MediaTestMixin


class TestImagesEndpoint(
    MediaTestMixin,
    FormDataMixin,
    WriteApiTestMixin,
    SiteContentCreateApiTestMixin,
    SiteContentDestroyApiTestMixin,
    BaseReadOnlyUncontrolledSiteContentApiTest,
):
    """
    End-to-end tests that the images endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:image-list"
    API_DETAIL_VIEW = "api:image-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.ImageFactory.create(site=site)

    def get_valid_data(self, site=None):
        """Returns a valid data object suitable for create/update requests"""
        return {
            "title": "A title for the media",
            "description": "Description of the media",
            "acknowledgement": "An acknowledgement of the media",
            "isShared": True,
            "excludeFromGames": True,
            "excludeFromKids": True,
            "original": self.get_sample_file("sample-image.jpg", "image/jpeg"),
        }

    def get_expected_response(self, instance, site):
        return self.get_expected_image_data(instance)

    def add_related_objects(self, instance):
        # related files are added as part of minimal instance; nothing extra to add here
        pass

    def assert_related_objects_deleted(self, instance):
        self.assert_instance_deleted(instance.original)
        self.assert_instance_deleted(instance.medium)
        self.assert_instance_deleted(instance.small)
        self.assert_instance_deleted(instance.thumbnail)
