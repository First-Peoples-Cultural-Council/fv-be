import json

import pytest

from backend.models.constants import Visibility
from backend.tests.test_apis.base.base_api_test import BaseApiTest


class ListApiTestMixin:
    """
    Basic tests for non-site-content list APIs. Use with BaseApiTest.

    Does NOT include permission-related tests.
    """

    def get_expected_list_response_item(self, instance):
        return self.get_expected_response(instance)

    @pytest.mark.django_db
    def test_list_empty(self):
        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

    @pytest.mark.django_db
    def test_list_minimal(self):
        instance = self.create_minimal_instance(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint())

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance
        )


class DetailApiTestMixin:
    """
    Basic tests for non-site-content detail APIs. Use with BaseApiTest.

    Does NOT include permission-related tests.
    """

    def get_expected_detail_response(self, instance):
        return self.get_expected_response(instance)

    @pytest.mark.django_db
    def test_detail_404(self):
        response = self.client.get(self.get_detail_endpoint("fake-key"))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_detail_minimal(self):
        instance = self.create_minimal_instance(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_detail_endpoint(key=instance.id))

        assert response.status_code == 200

        response_data = json.loads(response.content)

        assert response_data == self.get_expected_detail_response(instance)


class ReadOnlyApiTests(ListApiTestMixin, DetailApiTestMixin, BaseApiTest):
    pass
