from backend.models.media import Person
from backend.tests.factories import PersonFactory
from backend.tests.test_apis.base_api_test import BaseUncontrolledSiteContentApiTest


class TestPeopleEndpoints(BaseUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the /people endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:person-list"
    API_DETAIL_VIEW = "api:person-detail"
    model = Person

    def create_minimal_instance(self, site, visibility=None):
        return PersonFactory.create(site=site)

    def get_expected_response(self, instance, site):
        return {
            "url": f"http://testserver{self.get_detail_endpoint(instance.id, instance.site.slug)}",
            "id": str(instance.id),
            "name": instance.name,
            "bio": instance.bio,
        }

    def get_valid_data(self, site=None):
        return {
            "name": "Cool new name",
            "bio": "Cool new biography",
        }

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.name == expected_data["name"]
        assert actual_instance.bio == expected_data["bio"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["name"] == expected_data["name"]
        assert actual_response["bio"] == expected_data["bio"]

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass
