import json

from backend.models.constants import AppRole
from backend.tests.factories import get_app_admin

from .base_api_test import BaseApiTest


class TestPartsOfSpeechAPI(BaseApiTest):
    """Tests for parts-of-speech views."""

    FIXTURE_FILE = "partsOfSpeech_initial.json"
    API_LIST_VIEW = "api:partofspeech-list"
    API_DETAIL_VIEW = "api:partofspeech-detail"
    NUMBER_OF_PARTS_OF_SPEECH = 41

    def test_list_view(self, db):
        """Test that the list view returns the expected number of parts-of-speech."""

        member_user = get_app_admin(AppRole.STAFF)
        self.client.force_authenticate(user=member_user)
        response = self.client.get(self.get_list_endpoint())
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == self.NUMBER_OF_PARTS_OF_SPEECH

    def test_list_view_format(self, db):
        """Test that the list view returns the expected fields."""

        member_user = get_app_admin(AppRole.STAFF)
        self.client.force_authenticate(user=member_user)

        response = self.client.get(self.get_list_endpoint())
        response_data = json.loads(response.content)["results"]

        assert response.status_code == 200
        assert isinstance(response_data, list)
        assert len(response_data) > 0

        item = None
        for x in response_data:
            if x["parent"]:
                item = x
                break

        # Checking for required keys and their response structure
        assert "id" in item
        assert "title" in item
        assert "parent" in item

        assert isinstance(item["id"], str)
        assert isinstance(item["title"], str)
        assert isinstance(item["parent"], dict)

    def test_detail_view(self, db):
        """Test that the detail view returns the expected data."""
        member_user = get_app_admin(AppRole.STAFF)
        self.client.force_authenticate(user=member_user)

        response_list = self.client.get(self.get_list_endpoint(), format="json")
        list_data = json.loads(response_list.content)["results"]

        # Looking for a specific item with no children, to test the retrieve queryset
        # test will fail if fixture not loaded since there will be no items without any children in the response to
        # choose the first element from. If fixture is modified in such as way that all elements now have children at
        # top level, Create another fixture for testing purposes with one such element.
        for item in list_data:
            if item["parent"]:
                response = self.client.get(self.get_detail_endpoint(item["id"]))
                response_data = json.loads(response.content)
                break

        assert response.status_code == 200
        assert "id" in response_data
        assert "title" in response_data
        assert "parent" in response_data

        assert isinstance(response_data["id"], str)
        assert isinstance(response_data["title"], str)
        assert isinstance(response_data["parent"], dict)

    def test_detail_not_found(self, db):
        """Test that the detail view returns 404 for an invalid id."""

        member_user = get_app_admin(AppRole.STAFF)
        self.client.force_authenticate(user=member_user)
        response = self.client.get(self.get_detail_endpoint("invalid_id"))
        assert response.status_code == 404
