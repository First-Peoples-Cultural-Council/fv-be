import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.models.immersion_labels import ImmersionLabel
from backend.tests import factories

from .base_api_test import BaseUncontrolledSiteContentApiTest


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

    def create_minimal_instance(self, site, visibility):
        return factories.ImmersionLabelFactory(
            site=site,
            dictionary_entry=factories.DictionaryEntryFactory(
                site=site, visibility=visibility
            ),
        )

    def get_expected_detail_response(self, instance, site):
        return {
            "created": instance.created.astimezone().isoformat(),
            "createdBy": instance.created_by.email,
            "lastModified": instance.last_modified.astimezone().isoformat(),
            "lastModifiedBy": instance.last_modified_by.email,
            "id": str(instance.id),
            "url": f"http://testserver{self.get_detail_endpoint(instance.key, instance.site.slug)}",
            "site": {
                "id": str(site.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}",
                "title": site.title,
                "slug": site.slug,
                "visibility": instance.site.get_visibility_display().lower(),
                "language": site.language.title,
            },
            "dictionaryEntry": {
                "id": str(instance.dictionary_entry.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}/dictionary/{instance.dictionary_entry.id}",
                "title": instance.dictionary_entry.title,
                "type": instance.dictionary_entry.type,
                "translations": [],
                "relatedImages": [],
                "relatedAudio": [],
                "relatedVideos": [],
            },
            "key": str(instance.key),
        }

    def get_expected_response(self, instance, site):
        return self.get_expected_detail_response(instance, site)

    def get_valid_data(self, site=None):
        entry = factories.DictionaryEntryFactory(
            site=site, visibility=Visibility.PUBLIC
        )
        return {
            "dictionary_entry": str(entry.id),
            "key": self.TEST_KEY,
        }

    def get_valid_patch_data(self, site=None):
        entry = factories.DictionaryEntryFactory(site=site)
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

    @pytest.mark.skip(reason="Immersion label API does not have eligible null fields.")
    def test_create_with_nulls_success_201(self):
        # Immersion label API does not have eligible null fields.
        pass

    @pytest.mark.skip(reason="Immersion label API does not have eligible null fields.")
    def test_update_with_nulls_success_200(self):
        # Immersion label API does not have eligible null fields.
        pass

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
    def test_label_key_read_only(self):
        """
        Test that the immersion label key is read only after creation.
        """
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(site=site)
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
