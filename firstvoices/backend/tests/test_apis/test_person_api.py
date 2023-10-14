from backend.models.media import Person
from backend.tests import factories
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

    def get_valid_data_with_nulls(self, site=None):
        return {
            "name": "Cool new name",
        }

    def add_expected_defaults(self, data):
        return {
            **data,
            "bio": "",
        }

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.name == expected_data["name"]
        assert actual_instance.bio == expected_data["bio"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["name"] == expected_data["name"]
        assert actual_response["bio"] == expected_data["bio"]

    def assert_created_instance(self, pk, data):
        instance = Person.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass

    def create_original_instance_for_patch(self, site):
        return factories.PersonFactory.create(site=site, name="Name", bio="Bio")

    def get_valid_patch_data(self, site=None):
        return {"name": "Name Updated"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: Person
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.bio == original_instance.bio
        assert updated_instance.site == original_instance.site

    def assert_patch_instance_updated_fields(self, data, updated_instance: Person):
        assert updated_instance.name == data["name"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["name"] == data["name"]
        assert actual_response["bio"] == original_instance.bio
