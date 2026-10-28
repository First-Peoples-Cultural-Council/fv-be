import json
import uuid

import pytest

from backend.models import Organization
from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseUncontrolledSiteContentApiTest,
)
from backend.utils.uuid_utils import is_valid_uuid


class TestOrganizationEndpoints(BaseUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the gallery API endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:organization-list"
    API_DETAIL_VIEW = "api:organization-detail"

    model = Organization

    def create_minimal_instance(self, site, visibility):
        organization = factories.OrganizationFactory(site=site)
        return organization

    def create_original_instance_for_patch(self, site):
        return self.create_minimal_instance(site, "original")

    def get_expected_response(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        return {
            **standard_fields,
            "name": instance.name,
            "order": instance.order,
            "emails": instance.emails,
            "phoneNumbers": instance.phone_numbers,
            "address": instance.address,
            "contactMessage": instance.contact_message,
            "urlList": instance.url_list,
        }

    def get_valid_data(self, site=None):
        return {
            "name": "Test Organization",
            "order": 1,
            "emails": [
                {"id": str(uuid.uuid4()), "label": "primary", "value": "test@fpcc.ca"}
            ],
            "phoneNumbers": [
                {"id": str(uuid.uuid4()), "label": "work", "value": "1235551234"}
            ],
            "address": "123 Test St",
            "contactMessage": "Contact Message",
            "urlList": [
                {
                    "id": str(uuid.uuid4()),
                    "label": "support",
                    "value": "https://www.firstvoices.com/support",
                }
            ],
        }

    def get_valid_patch_data(self, site=None):
        return {
            "name": "New Organization",
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "name": "Test Organization",
        }

    def add_expected_defaults(self, data):
        return {
            "order": 0,
            "emails": [],
            "phoneNumbers": [],
            "address": "",
            "contactMessage": "Please contact us if you have any suggestions "
            "or feedback regarding our language content.",
            "urlList": [],
            **data,
        }

    def get_valid_data_with_null_optional_charfields(self, site=None):
        return {
            "name": "Test Organization",
            "order": 1,
            "emails": [],
            "phoneNumbers": [],
            "address": "",
            "contactMessage": "Please contact us if you have any suggestions "
            "or feedback regarding our language content.",
            "urlList": [],
        }

    def add_related_objects(self, instance):
        # No related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # No related objects to delete
        pass

    def assert_updated_instance(self, expected_data, actual_instance: Organization):
        assert actual_instance.name == expected_data["name"]
        assert actual_instance.order == expected_data["order"]
        for index, email in enumerate(expected_data["emails"]):
            assert is_valid_uuid(email["id"])
            assert email["label"] == expected_data["emails"][index]["label"]
        for index, phone in enumerate(expected_data["phoneNumbers"]):
            assert is_valid_uuid(phone["id"])
            assert phone["label"] == expected_data["phoneNumbers"][index]["label"]
        assert actual_instance.address == expected_data["address"]
        assert actual_instance.contact_message == expected_data["contactMessage"]
        for index, url in enumerate(expected_data["urlList"]):
            assert is_valid_uuid(url["id"])
            assert url["label"] == expected_data["urlList"][index]["label"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["name"] == expected_data["name"]
        assert actual_response["order"] == expected_data["order"]
        for index, email in enumerate(expected_data["emails"]):
            assert is_valid_uuid(actual_response["emails"][index]["id"])
            assert actual_response["emails"][index]["label"] == email["label"]
        for index, phone in enumerate(expected_data["phoneNumbers"]):
            assert is_valid_uuid(actual_response["phoneNumbers"][index]["id"])
            assert actual_response["phoneNumbers"][index]["label"] == phone["label"]
        assert actual_response["address"] == expected_data["address"]
        assert actual_response["contactMessage"] == expected_data["contactMessage"]
        for index, url in enumerate(expected_data["urlList"]):
            assert is_valid_uuid(actual_response["urlList"][index]["id"])
            assert actual_response["urlList"][index]["label"] == url["label"]

    def assert_created_instance(self, pk, data):
        instance = Organization.objects.get(pk=pk)
        self.assert_updated_instance(expected_data=data, actual_instance=instance)

    def assert_created_response(self, expected_data, actual_response):
        self.assert_update_response(
            expected_data=expected_data, actual_response=actual_response
        )

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        assert original_instance.order == updated_instance.order
        assert original_instance.emails == updated_instance.emails
        assert original_instance.phone_numbers == updated_instance.phone_numbers
        assert original_instance.address == updated_instance.address
        assert original_instance.contact_message == updated_instance.contact_message
        assert original_instance.url_list == updated_instance.url_list

    def assert_patch_instance_updated_fields(
        self, data, updated_instance: Organization
    ):
        assert updated_instance.name == data["name"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["name"] == data["name"]
        assert actual_response["order"] == original_instance.order
        assert actual_response["emails"] == original_instance.emails
        assert actual_response["phoneNumbers"] == original_instance.phone_numbers
        assert actual_response["address"] == original_instance.address
        assert actual_response["contactMessage"] == original_instance.contact_message
        assert actual_response["urlList"] == original_instance.url_list

    @pytest.mark.django_db
    def test_list_empty(self):
        # override empty list with default values for inactive organizations
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        expected_contact_message = (
            f"The FirstVoices site for the {site.title} language is currently inactive. "
            f"If this is your language or community and you are interested in working on "
            f"this project, please contact ltp@fpcc.ca for more information."
        )
        assert response_data["contactMessage"] == expected_contact_message
        assert response_data["emails"] == ["ltp@fpcc.ca"]
        assert response_data["urlList"] == ["https://www.firstvoices.com/support"]

    @pytest.mark.django_db
    def test_malformed_list_fields_400_create(self):
        site, user = factories.get_site_with_authenticated_member(
            client=self.client, role=Role.LANGUAGE_ADMIN
        )
        data = {"name": "Test Organization", "order": 1, "emails": [{"label": "email"}]}
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data,
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_malformed_list_fields_400_patch(self):
        site, user = factories.get_site_with_authenticated_member(
            client=self.client, role=Role.LANGUAGE_ADMIN
        )
        organization = factories.OrganizationFactory(site=site)
        data = {"emails": [{"label": "email"}]}
        response = self.client.patch(
            self.get_detail_endpoint(site_slug=site.slug, key=organization.id),
            data,
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_malformed_list_fields_400_put(self):
        site, user = factories.get_site_with_authenticated_member(
            client=self.client, role=Role.LANGUAGE_ADMIN
        )
        organization = factories.OrganizationFactory(site=site)
        data = {"name": "Test Organization", "order": 1, "emails": [{"label": "email"}]}
        response = self.client.put(
            self.get_detail_endpoint(site_slug=site.slug, key=organization.id),
            data,
            content_type="application/json",
        )
        assert response.status_code == 400
