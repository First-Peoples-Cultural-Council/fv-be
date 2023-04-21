import json

import pytest
from django.core.management import call_command
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import AppRole
from backend.tests.factories import get_app_admin


class TestPartsOfSpeechAPI:
    """Tests for parts-of-speech views."""

    FIXTURE_FILE = "partsOfSpeech_initial.json"
    API_LIST_VIEW = "api:parts-of-speech-list"
    API_DETAIL_VIEW = "api:parts-of-speech-detail"
    APP_NAME = "backend"

    @pytest.fixture(scope="session")
    def parts_of_speech_db_setup(self, django_db_setup, django_db_blocker):
        with django_db_blocker.unblock():
            call_command("loaddata", self.FIXTURE_FILE)

    def test_base_case_list_view(self, db, parts_of_speech_db_setup):
        # Testing the view returns a list of parts-of-speech

        client = APIClient()
        member_user = get_app_admin(AppRole.STAFF)
        client.force_authenticate(user=member_user)
        response = client.get(reverse(self.API_LIST_VIEW, current_app=self.APP_NAME))
        content = json.loads(response.content)["results"]

        assert response.status_code == 200
        assert len(content) > 0

    def test_retrieve_base_case(self, db, parts_of_speech_db_setup):
        """Test case for retrieve case to verify different querysets working for list and detail view."""

        client = APIClient()
        member_user = get_app_admin(AppRole.STAFF)
        client.force_authenticate(user=member_user)
        response_list = client.get(
            reverse(
                self.API_LIST_VIEW,
                current_app=self.APP_NAME,
            ),
            format="json",
        )
        content_list = json.loads(response_list.content)["results"]

        # Looking for a specific item with no children, to test the retrieve queryset
        # test will fail if fixture not loaded since there will be no items without any children in the response to
        # choose the first element from. If fixture is modified in such as way that all elements now have children at
        # top level, Create another fixture for testing purposes with one such element.
        items = [entry for entry in content_list if len(entry["children"]) == 0]
        item = items[0]
        pk = item["id"]

        response = client.get(
            reverse(self.API_DETAIL_VIEW, current_app="backend", args=[pk]),
            format="json",
        )
        response_obj = json.loads(response.content)

        assert response.status_code == 200
        assert "id" in response_obj
        assert "title" in response_obj
        assert "children" in response_obj

        assert isinstance(response_obj["id"], str)
        assert isinstance(response_obj["title"], str)
        assert isinstance(response_obj["children"], list)

    def test_retrieve_not_found(self, db, parts_of_speech_db_setup):
        # Testing the view returns 404 if parts of speech not found

        client = APIClient()
        member_user = get_app_admin(AppRole.STAFF)
        client.force_authenticate(user=member_user)
        response = client.get(
            reverse(
                self.API_DETAIL_VIEW,
                current_app=self.APP_NAME,
                args=["123_not_valid_key"],
            ),
            format="json",
        )
        assert response.status_code == 404

    def test_response_format_list_view(self, db, parts_of_speech_db_setup):
        # Testing the format of the content returned by list view for parts of speech

        client = APIClient()
        member_user = get_app_admin(AppRole.STAFF)
        client.force_authenticate(user=member_user)
        response = client.get(reverse(self.API_LIST_VIEW, current_app=self.APP_NAME))
        content = json.loads(response.content)["results"]

        assert isinstance(content, list)
        assert len(content) > 0

        sample_obj = content[1]

        # Checking for required keys and their response structure
        assert "id" in sample_obj
        assert "title" in sample_obj
        assert "children" in sample_obj

        assert isinstance(sample_obj["id"], str)
        assert isinstance(sample_obj["title"], str)
        assert isinstance(sample_obj["children"], list)
