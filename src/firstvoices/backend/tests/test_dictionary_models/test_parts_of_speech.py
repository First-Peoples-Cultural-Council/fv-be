import json

import pytest
from django.core.management import call_command
from django.shortcuts import get_list_or_404
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from firstvoices.backend.models.constants import AppRole
from firstvoices.backend.models.part_of_speech import PartOfSpeech
from firstvoices.backend.tests.factories import get_app_admin


# Fixtures
@pytest.fixture(scope="session")
def parts_of_speech_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "partsOfSpeech_initial.json")


class TestPartsOfSpeechModel:
    """Tests for parts-of-speech model."""

    def test_save_operation(self, db, parts_of_speech_db_setup):
        # Testing save operation for the model
        p1 = PartOfSpeech(
            title="part_of_speech_1",
            created=timezone.now(),
            last_modified=timezone.now(),
        )
        p1.save()
        p2 = PartOfSpeech(
            title="part_of_speech_2",
            parent=p1,
            created=timezone.now(),
            last_modified=timezone.now(),
        )
        p2.save()

        p1_fetch = PartOfSpeech.objects.get(title="part_of_speech_1")
        assert p1_fetch.title == "part_of_speech_1", "Title does not match"
        p2_fetch = PartOfSpeech.objects.get(title="part_of_speech_2")
        assert p2_fetch.title == "part_of_speech_2", "Title does not match"
        assert (
            p2_fetch.parent.title == "part_of_speech_1"
        ), "Parent's title does not match"

    def test_fixture_with_model(self, db, parts_of_speech_db_setup):
        # Testing that the fixture works, and we have at least 1 object in the database
        pos_count = get_list_or_404(PartOfSpeech)
        assert len(pos_count) != 0


class TestPartsOfSpeechView:
    """Tests for parts-of-speech views."""

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
