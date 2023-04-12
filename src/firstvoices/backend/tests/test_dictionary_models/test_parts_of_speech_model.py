import re

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.http.response import Http404
from django.shortcuts import get_list_or_404, get_object_or_404
from django.utils import timezone

from firstvoices.backend.models.constants import AppRole
from firstvoices.backend.models.part_of_speech import PartOfSpeech
from firstvoices.backend.tests.factories import get_app_admin


class TestPartsOfSpeechModel:
    """Tests for parts-of-speech model."""

    @pytest.fixture(scope="session")
    def parts_of_speech_db_setup(self, django_db_setup, django_db_blocker):
        with django_db_blocker.unblock():
            call_command("loaddata", "partsOfSpeech_initial.json")

    def test_save_operation(self, db):
        # Testing save operation for the model
        user = get_app_admin(AppRole.SUPERADMIN)

        p1 = PartOfSpeech(
            title="part_of_speech_1",
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=user,
            last_modified_by=user,
        )
        p1.save()
        p2 = PartOfSpeech(
            title="part_of_speech_2",
            parent=p1,
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=user,
            last_modified_by=user,
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

    def test_duplicate_titles_not_possible(self, db):
        # Testing that no duplicate titles are possible
        user = get_app_admin(AppRole.SUPERADMIN)

        p1 = PartOfSpeech(
            title="same_title",
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=user,
            last_modified_by=user,
        )
        p2 = PartOfSpeech(
            title="same_title",
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=user,
            last_modified_by=user,
        )
        with pytest.raises(
            ValidationError,
            match=re.escape(
                "{'title': ['Part Of Speech with this Title already exists.']}"
            ),
        ):
            p1.save()
            p2.save()

    def test_grandparents_not_allowed(self, db):
        # Testing that no grandparents should be allowed for parts of speech
        user = get_app_admin(AppRole.SUPERADMIN)

        p1 = PartOfSpeech(
            title="pos_1",
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=user,
            last_modified_by=user,
        )
        p2 = PartOfSpeech(
            title="pos_2",
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=user,
            last_modified_by=user,
            parent=p1,
        )
        p3 = PartOfSpeech(
            title="pos_3",
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=user,
            last_modified_by=user,
            parent=p2,
        )

        with pytest.raises(
            ValidationError,
            match=re.escape(
                "{'__all__': ['A PartOfSpeech may have a parent, but the parent PartOfSpeech"
                " cannot have a parent itself. (i.e. no grandparents)']}"
            ),
        ):
            p1.save()
            p2.save()
            p3.save()

    def test_superadmin_operations(self, db):
        # Test that super admin can create, update, get and delete a part of speech at model level
        user = get_app_admin(AppRole.SUPERADMIN)

        # Creating and updating
        p1 = PartOfSpeech(
            title="part_of_speech_1",
            created=timezone.now(),
            last_modified=timezone.now(),
            created_by=user,
            last_modified_by=user,
        )
        p1.title = "pos_2"
        p1.save()

        # Fetching and verifying
        p1_fetch = get_object_or_404(PartOfSpeech, title="pos_2")
        assert p1_fetch.title == "pos_2"

        # Deleting object and verifying
        p1.delete()
        with pytest.raises(Http404):
            get_object_or_404(PartOfSpeech, title="pos_2")
