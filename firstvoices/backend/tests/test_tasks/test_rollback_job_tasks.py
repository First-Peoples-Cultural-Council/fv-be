from unittest.mock import patch

import pytest
import tablib
from django.core.files.uploadedfile import SimpleUploadedFile

from backend.models import Audio
from backend.models.files import File
from backend.models.jobs import JobStatus
from backend.models.update_jobs import RollbackJob, UpdateJobStatus
from backend.tasks.rollback_job_tasks import rollback_update_job
from backend.tasks.update_job_tasks import confirm_update_job, validate_update_job
from backend.tasks.utils.update_job_utils import snapshot_entry, snapshot_update_entries
from backend.tests import factories


@pytest.mark.django_db
class TestRollbackJob:
    def setup_method(self):
        self.site = factories.SiteFactory()
        self.user = factories.get_superadmin()

    def create_update_job(self, headers, rows):
        data = tablib.Dataset(*rows, headers=headers)
        csv_file = SimpleUploadedFile(
            "update.csv", data.export("csv").encode("utf-8"), "text/csv"
        )
        file = factories.FileFactory(site=self.site, content=csv_file)
        return factories.UpdateJobFactory(
            site=self.site,
            run_as_user=self.user,
            status=UpdateJobStatus.ACCEPTED,
            validation_status=UpdateJobStatus.COMPLETE,
            data=file,
        )

    def create_rollback_job(self, update_job):
        return factories.RollbackJobFactory(
            update_job=update_job, created_by=self.user, last_modified_by=self.user
        )

    def test_snapshot_capture_ignores_invalid_ids_and_other_sites(self):
        entry = factories.DictionaryEntryFactory(site=self.site)
        other_site_entry = factories.DictionaryEntryFactory()
        update_job = factories.UpdateJobFactory(site=self.site)
        data = tablib.Dataset(
            [str(entry.id)],
            [str(entry.id)],
            [str(other_site_entry.id)],
            ["invalid-id"],
            [""],
            headers=["id"],
        )

        snapshots = snapshot_update_entries(data, update_job)

        assert snapshots == {str(entry.id): snapshot_entry(entry)}

    def test_missing_previous_job_aborts_restoration(self):
        # Rollback must restore the entry's link to its previous update job.
        # If that older job was deleted, rollback should fail without changing the entry.
        previous_job = factories.UpdateJobFactory(site=self.site)
        entry = factories.DictionaryEntryFactory(
            site=self.site, update_job=previous_job
        )

        update_job = self.create_update_job(
            headers=["id", "title"],
            rows=[[str(entry.id), "Updated title"]],
        )
        confirm_update_job(update_job.id)

        entry.refresh_from_db()
        updated_state = snapshot_entry(entry)
        previous_job.delete()
        rollback_job = self.create_rollback_job(update_job)

        rollback_update_job(rollback_job.id)

        entry.refresh_from_db()
        update_job.refresh_from_db()
        rollback_job.refresh_from_db()

        assert snapshot_entry(entry) == updated_state
        assert update_job.status == UpdateJobStatus.COMPLETE
        assert rollback_job.status == JobStatus.FAILED
        assert "missing update_job" in rollback_job.message

    def test_round_trip_restores_values_and_links_without_deleting_media(self):
        # Set up the original entry, its previous job, and all supported relationships.
        previous_job = factories.UpdateJobFactory(site=self.site)
        entry = factories.DictionaryEntryFactory(
            site=self.site, title="Original title", update_job=previous_job
        )
        category = factories.CategoryFactory(site=self.site)
        related_entry = factories.DictionaryEntryFactory(site=self.site)
        character = factories.CharacterFactory(site=self.site)
        old_audio = factories.AudioFactory(site=self.site)
        old_document = factories.DocumentFactory(site=self.site)
        old_image = factories.ImageFactory(site=self.site)
        old_video = factories.VideoFactory(site=self.site)
        entry.categories.set([category])
        entry.related_dictionary_entries.set([related_entry])
        entry.related_characters.set([character])
        entry.related_audio.set([old_audio])
        entry.related_documents.set([old_document])
        entry.related_images.set([old_image])
        entry.related_videos.set([old_video])
        original_state = snapshot_entry(entry)

        # Prepare an update that changes the title and replaces or clears selected links.
        new_audio = factories.AudioFactory(site=self.site)
        update_job = self.create_update_job(
            headers=[
                "id",
                "title",
                "category",
                "related_entry_ids",
                "audio_ids",
                "document_ids",
                "img_ids",
                "video_ids",
            ],
            rows=[
                [str(entry.id), "Updated title", "", "", str(new_audio.id), "", "", ""]
            ],
        )

        # Run the update and check its snapshots, and changed values.
        confirm_update_job(update_job.id)

        update_job.refresh_from_db()
        entry.refresh_from_db()
        assert update_job.status == UpdateJobStatus.COMPLETE
        assert (
            update_job.change_snapshot[str(entry.id)]["before_state"] == original_state
        )
        assert update_job.change_snapshot[str(entry.id)][
            "after_state"
        ] == snapshot_entry(entry)
        assert entry.title == "Updated title"
        assert entry.update_job_id == update_job.id
        assert list(entry.related_audio.all()) == [new_audio]

        # Run rollback, mocking the indexing request so it can be checked separately.
        rollback_job = self.create_rollback_job(update_job)
        with patch(
            "backend.tasks.rollback_job_tasks.request_sync_in_index"
        ) as mock_request_sync:
            rollback_update_job(rollback_job.id)

        # Check that the original values, previous job link, and relationships are restored.
        entry.refresh_from_db()
        update_job.refresh_from_db()
        rollback_job.refresh_from_db()
        assert entry.title == "Original title"
        assert entry.update_job_id == previous_job.id
        assert list(entry.categories.all()) == [category]
        assert list(entry.related_dictionary_entries.all()) == [related_entry]
        assert list(entry.related_characters.all()) == [character]
        assert list(entry.related_audio.all()) == [old_audio]
        assert list(entry.related_documents.all()) == [old_document]
        assert list(entry.related_images.all()) == [old_image]
        assert list(entry.related_videos.all()) == [old_video]
        # Also compare audit and derived fields, not just the visible content.
        assert snapshot_entry(entry) == original_state

        # Check completion statuses and confirm the snapshot is retained.
        assert update_job.status == UpdateJobStatus.ROLLED_BACK
        assert update_job.change_snapshot is not None
        assert rollback_job.status == JobStatus.COMPLETE
        assert rollback_job.conflicts == []

        # Media cleanup is deferred; rollback only restores the old relationships.
        assert Audio.objects.filter(id=new_audio.id).exists()
        assert File.objects.filter(id=new_audio.original_id).exists()

        # The restored entry must also be scheduled for search indexing.
        mock_request_sync.assert_called_once()

    def test_conflicts_are_reported_and_overridden(self):
        entry = factories.DictionaryEntryFactory(
            site=self.site, notes=["Original note"]
        )
        original_state = snapshot_entry(entry)

        update_job = self.create_update_job(
            headers=["id", "title"],
            rows=[[str(entry.id), "Updated title"]],
        )
        confirm_update_job(update_job.id)

        entry.refresh_from_db()
        entry.notes = ["Later edit"]
        entry.save()
        rollback_job = self.create_rollback_job(update_job)

        rollback_update_job(rollback_job.id)

        entry.refresh_from_db()
        rollback_job.refresh_from_db()
        assert entry.notes == ["Original note"]
        assert snapshot_entry(entry) == original_state
        assert rollback_job.status == JobStatus.COMPLETE
        assert len(rollback_job.conflicts) == 1
        assert rollback_job.conflicts[0]["id"] == str(entry.id)
        assert "notes" in rollback_job.conflicts[0]["fields"]

    def test_job_created_media_is_retained_after_rollback(self):
        entry = factories.DictionaryEntryFactory(site=self.site)
        original_state = snapshot_entry(entry)

        update_job = self.create_update_job(
            headers=["id", "title", "audio_filename"],
            rows=[[str(entry.id), "Updated title", "new_audio.mp3"]],
        )
        uploaded_file = factories.FileFactory(
            site=self.site,
            update_job=update_job,
            content=SimpleUploadedFile("new_audio.mp3", b"audio", "audio/mpeg"),
        )

        confirm_update_job(update_job.id)

        update_job.refresh_from_db()
        entry.refresh_from_db()
        assert update_job.status == UpdateJobStatus.COMPLETE
        audio = entry.related_audio.get()
        assert audio.original_id == uploaded_file.id
        rollback_job = self.create_rollback_job(update_job)

        rollback_update_job(rollback_job.id)

        entry.refresh_from_db()
        assert snapshot_entry(entry) == original_state
        assert Audio.objects.filter(id=audio.id).exists()
        assert File.objects.filter(id=uploaded_file.id).exists()
        assert uploaded_file.content.storage.exists(uploaded_file.content.name)

    def test_only_successful_rows_have_snapshots(self):
        valid_entry = factories.DictionaryEntryFactory(site=self.site)
        invalid_entry = factories.DictionaryEntryFactory(site=self.site)
        update_job = self.create_update_job(
            headers=["id", "title", "type"],
            rows=[
                [str(valid_entry.id), "Updated title", "word"],
                [str(invalid_entry.id), "Random title", "invalid type"],
            ],
        )

        confirm_update_job(update_job.id)

        update_job.refresh_from_db()
        assert update_job.status == UpdateJobStatus.COMPLETE
        assert set(update_job.change_snapshot) == {str(valid_entry.id)}

    def test_validation_does_not_create_snapshot(self):
        entry = factories.DictionaryEntryFactory(site=self.site)
        original_state = snapshot_entry(entry)

        update_job = self.create_update_job(
            headers=["id", "title"],
            rows=[[str(entry.id), "Updated title"]],
        )
        update_job.status = None
        update_job.validation_status = UpdateJobStatus.ACCEPTED
        update_job.save()

        validate_update_job(update_job.id)

        update_job.refresh_from_db()
        entry.refresh_from_db()
        assert update_job.change_snapshot is None
        assert update_job.rollback_expires_at is None
        assert snapshot_entry(entry) == original_state

    def test_missing_entry_aborts_whole_rollback(self):
        first_entry = factories.DictionaryEntryFactory(site=self.site)
        second_entry = factories.DictionaryEntryFactory(site=self.site)

        update_job = self.create_update_job(
            headers=["id", "title"],
            rows=[
                [str(first_entry.id), "Updated title"],
                [str(second_entry.id), "Updated title"],
            ],
        )
        confirm_update_job(update_job.id)

        first_entry.refresh_from_db()
        updated_state = snapshot_entry(first_entry)
        second_entry.delete()

        rollback_job = self.create_rollback_job(update_job)
        rollback_update_job(rollback_job.id)

        first_entry.refresh_from_db()
        update_job.refresh_from_db()
        rollback_job.refresh_from_db()
        assert snapshot_entry(first_entry) == updated_state
        assert update_job.status == UpdateJobStatus.COMPLETE
        assert rollback_job.status == JobStatus.FAILED
        assert "missing" in rollback_job.message

    def test_missing_old_media_aborts_whole_rollback(self):
        first_entry = factories.DictionaryEntryFactory(site=self.site)
        second_entry = factories.DictionaryEntryFactory(site=self.site)
        audio = factories.AudioFactory(site=self.site)
        second_entry.related_audio.set([audio])

        update_job = self.create_update_job(
            headers=["id", "title", "audio_ids"],
            rows=[
                [str(first_entry.id), "Updated title", ""],
                [str(second_entry.id), "Updated title", ""],
            ],
        )
        confirm_update_job(update_job.id)

        first_entry.refresh_from_db()
        second_entry.refresh_from_db()
        first_updated_state = snapshot_entry(first_entry)
        second_updated_state = snapshot_entry(second_entry)
        audio.delete()
        rollback_job = self.create_rollback_job(update_job)

        rollback_update_job(rollback_job.id)

        first_entry.refresh_from_db()
        second_entry.refresh_from_db()
        update_job.refresh_from_db()
        rollback_job.refresh_from_db()

        assert snapshot_entry(first_entry) == first_updated_state
        assert snapshot_entry(second_entry) == second_updated_state
        assert update_job.status == UpdateJobStatus.COMPLETE
        assert rollback_job.status == JobStatus.FAILED
        assert "missing" in rollback_job.message

    def test_restore_failure_rolls_back_previous_entries_and_keeps_error(self):
        first_entry = factories.DictionaryEntryFactory(site=self.site)
        second_entry = factories.DictionaryEntryFactory(site=self.site)
        entries = [first_entry, second_entry]

        update_job = self.create_update_job(
            headers=["id", "title"],
            rows=[[str(entry.id), "Updated title"] for entry in entries],
        )
        confirm_update_job(update_job.id)

        updated_states = {}
        for entry in entries:
            entry.refresh_from_db()
            updated_states[str(entry.id)] = snapshot_entry(entry)
        rollback_job = self.create_rollback_job(update_job)

        # Fail after the first entry was restored to verify the transaction undoes it.
        with patch(
            "backend.tasks.rollback_job_tasks.request_sync_in_index",
            side_effect=[None, RuntimeError("Restoration failed")],
        ) as mock_request_sync:
            rollback_update_job(rollback_job.id)

        rollback_job.refresh_from_db()
        update_job.refresh_from_db()
        assert mock_request_sync.call_count == 2
        assert rollback_job.status == JobStatus.FAILED
        assert rollback_job.message == "Restoration failed"
        assert update_job.status == UpdateJobStatus.COMPLETE

        for entry in entries:
            entry.refresh_from_db()
            assert snapshot_entry(entry) == updated_states[str(entry.id)]

    def test_completed_rollback_does_not_run_again(self):
        # Complete an update and its rollback before simulating a repeated worker call.
        entry = factories.DictionaryEntryFactory(site=self.site)
        update_job = self.create_update_job(
            headers=["id", "title"],
            rows=[[str(entry.id), "Updated title"]],
        )
        confirm_update_job(update_job.id)

        rollback_job = self.create_rollback_job(update_job)
        rollback_update_job(rollback_job.id)

        # A later edit must not be overwritten by running the same rollback again.
        entry.refresh_from_db()
        entry.title = "Edit after rollback"
        entry.save()
        edited_state = snapshot_entry(entry)

        # The completed rollback should be ignored, preserving the edit and job statuses.
        rollback_update_job(rollback_job.id)

        entry.refresh_from_db()
        update_job.refresh_from_db()
        rollback_job.refresh_from_db()

        assert snapshot_entry(entry) == edited_state
        assert update_job.status == UpdateJobStatus.ROLLED_BACK
        assert rollback_job.status == JobStatus.COMPLETE

    @pytest.mark.parametrize("task", [validate_update_job, confirm_update_job])
    def test_rolled_back_update_job_cannot_run_again(self, task):
        entry = factories.DictionaryEntryFactory(site=self.site)
        update_job = self.create_update_job(
            headers=["id", "title"],
            rows=[[str(entry.id), "Updated title"]],
        )
        confirm_update_job(update_job.id)

        rollback_job = self.create_rollback_job(update_job)
        rollback_update_job(rollback_job.id)

        entry.refresh_from_db()
        entry.title = "Edit after rollback"
        entry.save()
        edited_state = snapshot_entry(entry)

        task(update_job.id)

        entry.refresh_from_db()
        update_job.refresh_from_db()
        assert snapshot_entry(entry) == edited_state
        assert update_job.status == UpdateJobStatus.ROLLED_BACK

    def test_cascade_deletes_rollback_record(self):
        update_job = factories.UpdateJobFactory(site=self.site)
        rollback_job = self.create_rollback_job(update_job)

        update_job.delete()

        assert not RollbackJob.objects.filter(id=rollback_job.id).exists()
