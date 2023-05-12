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

    def get_list_endpoint(self, **kwargs):
        return reverse(self.API_LIST_VIEW, current_app=self.APP_NAME)

    def get_detail_endpoint(self, key, **kwargs):
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
            self.API_DETAIL_VIEW, current_app=self.APP_NAME, args=[site_slug, key]
        )

    def setup_method(self):
        self.client = APIClient()

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
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=visibility)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_list_empty(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    @pytest.mark.django_db
    def test_detail_404_unknown_key(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_detail_endpoint(key="fake-key", site_slug=site.slug)
        )

        assert response.status_code == 404


class BaseSiteControlledContentApiTest(BaseSiteContentApiTest):
    """
    Minimal setup for controlled site content api integration testing.
    """

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
