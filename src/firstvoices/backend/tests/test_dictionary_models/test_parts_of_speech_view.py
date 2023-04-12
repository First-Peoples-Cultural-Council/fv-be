import json

import pytest
from django.core.management import call_command
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from firstvoices.backend.models.constants import AppRole
from firstvoices.backend.tests.factories import get_app_admin


class TestPartsOfSpeechView:
    """Tests for parts-of-speech views."""

    @pytest.fixture(scope="session")
    def parts_of_speech_db_setup(self, django_db_setup, django_db_blocker):
        with django_db_blocker.unblock():
            call_command("loaddata", "partsOfSpeech_initial.json")

    def test_base_case_list_view(self, db, parts_of_speech_db_setup):
        # Testing the view returns a list of parts-of-speech

        client = APIClient()
        member_user = get_app_admin(AppRole.STAFF)
        client.force_authenticate(user=member_user)
        response = client.get(
            reverse("api:parts-of-speech-list", current_app="backend")
        )
        content = json.loads(response.content)

        assert response.status_code == 200
        assert len(content) > 0

    def test_retrieve_not_found(self, db, parts_of_speech_db_setup):
        # Testing the view returns 404 if parts of speech not found

        client = APIClient()
        member_user = get_app_admin(AppRole.STAFF)
        client.force_authenticate(user=member_user)
        response = client.get(
            reverse(
                "api:parts-of-speech-detail",
                current_app="backend",
                args=["123_not_valid_key"],
            ),
            format="json",
        )
        assert response.status_code == 404

    def test_response_format_list(self, db, parts_of_speech_db_setup):
        # Testing the format of the content returned by list view for parts of speech

        client = APIClient()
        member_user = get_app_admin(AppRole.STAFF)
        client.force_authenticate(user=member_user)
        response = client.get(
            reverse("api:parts-of-speech-list", current_app="backend")
        )
        content = json.loads(response.content)

        assert type(content) == list
        assert len(content) > 0

        sample_obj = content[1]

        # Checking for required keys and their response structure
        assert "id" in sample_obj
        assert "title" in sample_obj
        assert "parent" in sample_obj

        assert isinstance(sample_obj["id"], str)
        assert isinstance(sample_obj["title"], str)
        assert isinstance(sample_obj["parent"], str) or isinstance(
            sample_obj["parent"], type(None)
        )
