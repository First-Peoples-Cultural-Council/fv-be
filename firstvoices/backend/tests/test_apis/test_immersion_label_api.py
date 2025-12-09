import json

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.models.immersion_labels import ImmersionLabel
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseUncontrolledSiteContentApiTest,
)
from backend.tests.test_apis.test_dictionary_api import (
    assert_dictionary_entry_summary_response,
)
from backend.tests.utils import format_dictionary_entry_related_field


class TestImmersionEndpoints(BaseUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the immersion label endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:immersionlabel-list"
    API_DETAIL_VIEW = "api:immersionlabel-detail"
    TEST_KEY = "test_key"

    model = ImmersionLabel

    def get_lookup_key(self, instance):
        return instance.key

    def create_minimal_instance(self, site, visibility=Visibility.PUBLIC):
        return factories.ImmersionLabelFactory(
            site=site,
            dictionary_entry=factories.DictionaryEntryFactory(
                site=site, visibility=visibility
            ),
        )

    def get_expected_response(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        standard_fields["url"] = (
            f"http://testserver{self.get_detail_endpoint(instance.key, instance.site.slug)}"
        )
        return {
            **standard_fields,
            "dictionaryEntry": {
                "id": str(instance.dictionary_entry.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}/dictionary/{instance.dictionary_entry.id}",
                "title": instance.dictionary_entry.title,
                "type": instance.dictionary_entry.type,
                "translations": format_dictionary_entry_related_field(
                    instance.dictionary_entry.translations
                ),
                "relatedAudio": [],
                "relatedDocuments": [],
                "relatedImages": [],
                "relatedVideos": [],
                "relatedVideoLinks": [],
            },
            "key": str(instance.key),
        }

    def assert_minimal_list_response(self, response, instance):
        """Customized to handle dynamically added stub IDs from the serializers."""
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 1

        response_item = response_data["results"][0]
        assert "id" in response_item["dictionaryEntry"]["translations"][0]
        del response_item["dictionaryEntry"]["translations"][0]["id"]

        assert response_item == self.get_expected_list_response_item(
            instance, instance.site
        )

    def assert_minimal_list_response_no_email_access(self, response, instance):
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 1

        response_item = response_data["results"][0]
        assert "id" in response_item["dictionaryEntry"]["translations"][0]
        del response_item["dictionaryEntry"]["translations"][0]["id"]

        assert response_item == self.get_expected_list_response_item_no_email_access(
            instance, instance.site
        )

    def get_valid_data(self, site=None):
        entry = factories.DictionaryEntryFactory(
            site=site, visibility=Visibility.PUBLIC
        )
        return {
            "dictionary_entry": str(entry.id),
            "key": self.TEST_KEY,
        }

    def get_valid_patch_data(self, site=None):
        entry = factories.DictionaryEntryFactory(
            site=site, visibility=Visibility.PUBLIC
        )
        return {
            "dictionary_entry": str(entry.id),
        }

    def add_expected_defaults(self, data):
        return data

    def assert_updated_instance(self, expected_data, actual_instance):
        assert (
            str(actual_instance.dictionary_entry.id)
            == expected_data["dictionary_entry"]
        )

    def assert_update_response(self, expected_data, actual_response):
        assert (
            actual_response["dictionaryEntry"]["id"]
            == expected_data["dictionary_entry"]
        )

    def assert_created_instance(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        assert str(instance.key) == data["key"]
        assert str(instance.dictionary_entry.id) == data["dictionary_entry"]

    def assert_created_response(self, expected_data, actual_response):
        assert actual_response["key"] == expected_data["key"]
        assert (
            actual_response["dictionaryEntry"]["id"]
            == expected_data["dictionary_entry"]
        )

    def create_original_instance_for_patch(self, site):
        return self.create_minimal_instance(site, Visibility.PUBLIC)

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance
    ):
        assert original_instance.key == updated_instance.key

    def assert_patch_instance_updated_fields(self, data, updated_instance):
        assert str(updated_instance.dictionary_entry.id) == data["dictionary_entry"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert original_instance.key == actual_response["key"]
        assert actual_response["dictionaryEntry"]["id"] == data["dictionary_entry"]

    def assert_immersion_label_response(self, instance, response_data, request_data):
        standard_fields = self.get_expected_standard_fields(instance, instance.site)
        standard_fields["url"] = (
            f"http://testserver{self.get_detail_endpoint(instance.key, instance.site.slug)}"
        )
        for key, value in standard_fields.items():
            assert response_data[key] == value

        assert response_data["key"] == str(instance.key)
        assert_dictionary_entry_summary_response(
            response_data["dictionaryEntry"], instance.dictionary_entry, request_data
        )

    @pytest.mark.skip(reason="Immersion label API does not have eligible null fields.")
    def test_create_with_nulls_success_201(self):
        # Immersion label API does not have eligible null fields.
        pass

    @pytest.mark.skip(reason="Immersion label API does not have eligible null fields.")
    def test_update_with_nulls_success_200(self):
        # Immersion label API does not have eligible null fields.
        pass

    @pytest.mark.skip(
        reason="Immersion label API does not have eligible optional charfields."
    )
    def test_create_with_null_optional_charfields_success_201(self):
        # Immersion label API does not have eligible optional charfields.
        pass

    @pytest.mark.skip(
        reason="Immersion label API does not have eligible optional charfields."
    )
    def test_update_with_null_optional_charfields_success_200(self):
        # Immersion label API does not have eligible optional charfields.
        pass

    @pytest.mark.django_db
    def test_detail_minimal(self):
        # overwriting the base test to test text list field ids
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.perform_successful_get_request_response(instance, site, True)
        request_data = response.wsgi_request
        response_data = json.loads(response.content)

        self.assert_immersion_label_response(instance, response_data, request_data)

    @pytest.mark.django_db
    def test_list_minimal(self):
        # overwriting the base test to test text list field ids
        site, user = factories.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.perform_successful_get_request_response(instance, site, False)
        request_data = response.wsgi_request
        response_data = json.loads(response.content)["results"][0]

        self.assert_immersion_label_response(instance, response_data, request_data)

    @pytest.mark.django_db
    def test_dictionary_entry_same_site_validation(self):
        """
        Tests that a validation error is raised if the dictionary entry and immersion label are not in the same site.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create()
        site2 = factories.SiteFactory.create()
        entry = factories.DictionaryEntryFactory.create(site=site2)

        data = {
            "dictionary_entry": str(entry.id),
            "key": self.TEST_KEY,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_dictionary_entry_visibility_validation(self):
        """
        Tests that a validation error is raised if the dictionary entry's visibility is less than the site's.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.TEAM
        )

        data = {
            "dictionary_entry": str(entry.id),
            "key": self.TEST_KEY,
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug), format="json", data=data
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_labels_ordered_by_key(self):
        """
        Tests that the labels are ordered alphabetically by key.
        """
        site, user = factories.access.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        entry1 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry3 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        factories.ImmersionLabelFactory.create(
            site=site, dictionary_entry=entry1, key="b"
        )
        factories.ImmersionLabelFactory.create(
            site=site, dictionary_entry=entry2, key="c"
        )
        factories.ImmersionLabelFactory.create(
            site=site, dictionary_entry=entry3, key="a"
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        assert len(response.data["results"]) == 3
        assert response.data["results"][0]["key"] == "a"
        assert response.data["results"][1]["key"] == "b"
        assert response.data["results"][2]["key"] == "c"

    @pytest.mark.django_db
    def test_immersion_map_permissions(self):
        """
        Tests that the immersion map endpoint only shows viewable labels.
        """
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry1 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.MEMBERS
        )
        entry3 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.TEAM
        )
        factories.ImmersionLabelFactory.create(site=site, dictionary_entry=entry1)
        factories.ImmersionLabelFactory.create(site=site, dictionary_entry=entry2)
        factories.ImmersionLabelFactory.create(site=site, dictionary_entry=entry3)

        user = factories.UserFactory.create()
        factories.MembershipFactory.create(
            site=site, user=user, role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.get_list_endpoint(site.slug) + "/all")

        assert response.status_code == 200
        assert len(response.data) == 3

        user = factories.UserFactory.create()
        factories.MembershipFactory.create(site=site, user=user, role=Role.MEMBER)
        self.client.force_authenticate(user=user)
        response = self.client.get(self.get_list_endpoint(site.slug) + "/all")

        assert response.status_code == 200
        assert len(response.data) == 2

        user = factories.access.get_non_member_user()
        self.client.force_authenticate(user=user)
        response = self.client.get(self.get_list_endpoint(site.slug) + "/all")

        assert response.status_code == 200
        assert len(response.data) == 1

    @pytest.mark.django_db
    def test_immersion_map_empty(self):
        """
        Tests that the immersion map endpoint returns an empty object if there are no labels.
        """
        site, user = factories.access.get_site_with_member(
            Visibility.MEMBERS, Role.MEMBER
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(self.get_list_endpoint(site.slug) + "/all")

        assert response.status_code == 200
        assert response.data == {}

    @pytest.mark.django_db
    def test_immersion_map(self):
        """
        Tests that the immersion map endpoint returns a map with the correct data.
        """
        site, user = factories.access.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        entry = factories.DictionaryEntryFactory.create(site=site)
        entry2 = factories.DictionaryEntryFactory.create(site=site)
        factories.ImmersionLabelFactory.create(
            site=site, dictionary_entry=entry, key=self.TEST_KEY
        )
        factories.ImmersionLabelFactory.create(
            site=site, dictionary_entry=entry2, key="test_key2"
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(self.get_list_endpoint(site.slug) + "/all")

        assert response.status_code == 200
        assert response.data[self.TEST_KEY] == str(entry.title)
        assert response.data["test_key2"] == str(entry2.title)

    @pytest.mark.django_db
    def test_immersion_map_only_one_site(self):
        """
        Tests that the immersion map endpoint only returns labels from the correct site.
        """
        site, user = factories.access.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        site2 = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.MembershipFactory.create(
            site=site2, user=user, role=Role.LANGUAGE_ADMIN
        )

        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(
            site=site2, visibility=Visibility.PUBLIC
        )
        factories.ImmersionLabelFactory.create(
            site=site, dictionary_entry=entry, key=self.TEST_KEY
        )
        factories.ImmersionLabelFactory.create(
            site=site2, dictionary_entry=entry2, key="test_key2"
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(self.get_list_endpoint(site.slug) + "/all")

        assert response.status_code == 200
        assert response.data[self.TEST_KEY] == str(entry.title)
        assert "test_key2" not in response.data

    @pytest.mark.django_db
    def test_immersion_map_ordered_by_key(self):
        """
        Tests that the immersion map endpoint is ordered alphabetically by key.
        """
        site, user = factories.access.get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        entry1 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry3 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        factories.ImmersionLabelFactory.create(
            site=site, dictionary_entry=entry1, key="c"
        )
        factories.ImmersionLabelFactory.create(
            site=site, dictionary_entry=entry2, key="a"
        )
        factories.ImmersionLabelFactory.create(
            site=site, dictionary_entry=entry3, key="b"
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(self.get_list_endpoint(site.slug) + "/all")

        assert response.status_code == 200
        assert list(response.data.keys()) == ["a", "b", "c"]

    @pytest.mark.django_db
    def test_label_key_read_only(self):
        """
        Test that the immersion label key is read only after creation.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        label = factories.ImmersionLabelFactory.create(site=site)

        data = {
            "key": "new_key",
            "dictionary_entry": str(entry.id),
        }

        response = self.client.put(
            self.get_detail_endpoint(key=label.key, site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["key"] == label.key

    @pytest.mark.django_db
    def test_label_keys_only_unique_per_site(self):
        """
        Test that the immersion label keys are unique per site, but the same key can be used in multiple sites.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        site2 = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(
            site=site2, visibility=Visibility.PUBLIC
        )

        data = {
            "key": self.TEST_KEY,
            "dictionary_entry": str(entry.id),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 201

        data = {
            "key": self.TEST_KEY,
            "dictionary_entry": str(entry2.id),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site2.slug),
            format="json",
            data=data,
        )

        assert response.status_code == 201
