import pytest
from django.conf import settings
from django.core.cache import caches
from rest_framework.test import APIClient

from backend.models.constants import Role
from backend.tests import factories
from backend.tests.test_apis.base.base_api_test import BaseApiTest


class TestThrottling(BaseApiTest):
    API_LIST_VIEW = "api:site-list"

    def setup_method(self):
        self.client = APIClient()
        self.site = factories.SiteFactory.create()
        self.user = factories.UserFactory.create()
        caches["throttle"].clear()

    @pytest.fixture
    def use_burst_rate(self):
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["burst"] = "3/min"
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["sustained"] = "1000/day"
        yield "settings"
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["burst"] = "200/min"
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["sustained"] = "2000/day"

    @pytest.fixture
    def use_sustained_rate(self):
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["burst"] = "1000/min"
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["sustained"] = "3/day"
        yield "settings"
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["burst"] = "200/min"
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["sustained"] = "2000/day"

    def run_throttling_test(self, user_role):
        if user_role:
            factories.MembershipFactory.create(
                user=self.user, site=self.site, role=user_role
            )
        self.client.force_authenticate(user=self.user)

        for _ in range(0, 3):
            response = self.client.get(self.get_list_endpoint())
            assert response.status_code == 200

        response = self.client.get(self.get_list_endpoint())
        assert response.status_code == 429

    @pytest.mark.usefixtures("use_burst_rate")
    @pytest.mark.parametrize(
        "user_role",
        [None, Role.MEMBER, Role.EDITOR, Role.ASSISTANT, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.django_db
    def test_throttling_burst_limit(self, user_role):
        self.run_throttling_test(user_role)

    @pytest.mark.usefixtures("use_sustained_rate")
    @pytest.mark.parametrize(
        "user_role",
        [None, Role.MEMBER, Role.EDITOR, Role.ASSISTANT, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.django_db
    def test_throttling_sustained_limit(self, user_role):
        self.run_throttling_test(user_role)
