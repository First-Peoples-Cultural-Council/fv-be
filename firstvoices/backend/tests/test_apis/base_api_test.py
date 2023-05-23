import json

import pytest
from django.utils.http import urlencode
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.tests import factories


class BaseApiTest:
    """
    Minimal setup for api integration testing.
    """

    API_LIST_VIEW = ""  # E.g., "api:site-list"
    API_DETAIL_VIEW = ""  # E.g., "api:site-detail"
    APP_NAME = "backend"

    client = None

    def get_list_endpoint(self):
        return reverse(self.API_LIST_VIEW, current_app=self.APP_NAME)

    def get_detail_endpoint(self, key):
        return reverse(self.API_DETAIL_VIEW, current_app=self.APP_NAME, args=[key])

    def setup_method(self):
        self.client = APIClient()


class BaseSiteContentApiTest:
    """
    Minimal setup for site content api integration testing.
    """

    API_LIST_VIEW = ""  # E.g., "api:site-list"
    API_DETAIL_VIEW = ""  # E.g., "api:site-detail"
    APP_NAME = "backend"

    client = None

    def get_list_endpoint(self, site_slug, query_kwargs=None):
        """
        query_kwargs accept query parameters e.g. query_kwargs={"contains": "WORD"}
        """
        url = reverse(self.API_LIST_VIEW, current_app=self.APP_NAME, args=[site_slug])
        if query_kwargs:
            return f"{url}?{urlencode(query_kwargs)}"
        return url

    def get_detail_endpoint(self, key, site_slug):
        return reverse(
            self.API_DETAIL_VIEW, current_app=self.APP_NAME, args=[site_slug, str(key)]
        )

    def setup_method(self):
        self.client = APIClient()

    def create_site_with_non_member(self, site_visibility):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=site_visibility)

        return site

    def create_minimal_instance(self, site, visibility):
        raise NotImplementedError()

    def get_expected_response(self, instance, site):
        raise NotImplementedError()


class ListApiTestMixin:
    """
    For use with BaseSiteContentApiTest
    """

    def get_expected_list_response_item(self, instance, site):
        return self.get_expected_response(instance, site)

    @pytest.mark.django_db
    def test_list_404_site_not_found(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site_slug="missing-site"))

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.django_db
    def test_list_403_site_not_visible(self, visibility):
        site = self.create_site_with_non_member(visibility)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_list_empty(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_list_member_access(self, role):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_list_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_list_minimal(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance, site
        )


class DetailApiTestMixin:
    """
    For use with BaseSiteContentApiTest
    """

    def get_expected_detail_response(self, instance, site):
        return self.get_expected_response(instance, site)

    @pytest.mark.django_db
    def test_detail_404_unknown_key(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        response = self.client.get(
            self.get_detail_endpoint(key="fake-key", site_slug=site.slug)
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_detail_404_site_not_found(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug="invalid")
        )

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_detail_403_site_not_visible(self):
        site = self.create_site_with_non_member(Visibility.MEMBERS)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_detail_member_access(self, role):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(
            site=site, visibility=Visibility.MEMBERS
        )

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_list_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_detail_minimal(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)
        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == self.get_expected_detail_response(instance, site)


class ListPermissionsApiTestMixin:
    @pytest.mark.django_db
    def test_list_permissions(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        self.create_minimal_instance(site=site, visibility=Visibility.MEMBERS)
        self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance, site
        )


class DetailPermissionsApiTestMixin:
    """
    Additional test cases for items with their own visibility settings, suitable for testing APIs related to
    BaseControlledSiteContentModel.
    """

    @pytest.mark.django_db
    def test_detail_403_entry_not_visible(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_detail_endpoint(key=instance.id, site_slug=site.slug)
        )

        assert response.status_code == 403


class BaseControlledSiteContentApiTest(
    ListApiTestMixin,
    ListPermissionsApiTestMixin,
    DetailApiTestMixin,
    DetailPermissionsApiTestMixin,
    BaseSiteContentApiTest,
):
    pass


class BaseUncontrolledSiteContentApiTest(
    ListApiTestMixin, DetailApiTestMixin, BaseSiteContentApiTest
):
    pass
