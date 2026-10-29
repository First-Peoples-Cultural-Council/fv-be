import json
from datetime import timedelta
from unittest.mock import patch

import pytest
import tablib
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import AppRole, Role
from backend.models.jobs import JobStatus
from backend.models.update_jobs import RollbackJob, UpdateJobStatus
from backend.tasks.update_job_tasks import confirm_update_job
from backend.tasks.utils.update_job_utils import snapshot_entry
from backend.tests import factories
from backend.tests.utils import TransactionOnCommitMixin


@pytest.mark.django_db
class TestUpdateJobRollbackApi(TransactionOnCommitMixin):
    API_ROLLBACK_ACTION = "api:updatejob-rollback"

    def setup_method(self):
        self.client = APIClient()
        self.site, self.user = factories.get_site_with_app_admin(self.client)
        self.job = factories.UpdateJobFactory(
            site=self.site,
            status=UpdateJobStatus.COMPLETE,
            validation_status=UpdateJobStatus.COMPLETE,
            change_snapshot={},
            rollback_expires_at=timezone.now() + timedelta(days=7),
        )

    def get_rollback_endpoint(self):
        return reverse(self.API_ROLLBACK_ACTION, args=[self.site.slug, self.job.id])

    @pytest.mark.parametrize("role", [AppRole.STAFF, AppRole.SUPERADMIN])
    def test_staff_can_request_and_view_rollback(self, role):
        user = factories.get_app_admin(role)
        self.client.force_authenticate(user=user)

        with patch(
            "backend.views.update_job_views.rollback_update_job.apply_async"
        ) as mock_apply_async:
            # Run the on-commit callback without starting the rollback worker.
            with self.capture_on_commit_callbacks(execute=True):
                response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 202

        response_data = json.loads(response.content)
        rollback_job = RollbackJob.objects.get(update_job=self.job)
        assert rollback_job.created_by == user
        assert rollback_job.last_modified_by == user
        assert rollback_job.status == JobStatus.ACCEPTED
        assert rollback_job.message is None
        assert rollback_job.task_id is None
        assert rollback_job.conflicts == []
        assert response_data["id"] == str(rollback_job.id)

        mock_apply_async.assert_called_once()
        assert mock_apply_async.call_args.args == ((str(rollback_job.id),),)

        response = self.client.get(self.get_rollback_endpoint())

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["conflicts"] == []
        assert "changeSnapshot" not in response_data

    @pytest.mark.parametrize(
        "role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    def test_site_roles_cannot_request_or_view(self, role):
        user = factories.UserFactory()
        factories.MembershipFactory(site=self.site, user=user, role=role)
        self.client.force_authenticate(user=user)

        post_response = self.client.post(self.get_rollback_endpoint())
        get_response = self.client.get(self.get_rollback_endpoint())

        assert post_response.status_code == 403
        assert get_response.status_code == 403

    def test_anonymous_cannot_request_or_view(self):
        self.client.force_authenticate(user=None)

        post_response = self.client.post(self.get_rollback_endpoint())
        get_response = self.client.get(self.get_rollback_endpoint())

        assert post_response.status_code == 401
        assert get_response.status_code == 401

    def test_update_request_and_worker_restore_entry_end_to_end(self):
        entry = factories.DictionaryEntryFactory(site=self.site, title="Before")
        original_state = snapshot_entry(entry)
        data = tablib.Dataset([str(entry.id), "After"], headers=["id", "title"])

        self.job.data = factories.FileFactory(
            site=self.site,
            content=SimpleUploadedFile("update.csv", data.csv.encode(), "text/csv"),
        )
        self.job.run_as_user = self.user
        self.job.status = UpdateJobStatus.ACCEPTED
        self.job.save()

        confirm_update_job(self.job.id)
        entry.refresh_from_db()
        assert entry.title == "After"

        with patch("backend.tasks.rollback_job_tasks.request_sync_in_index"):
            # Test that the rollback request triggers the worker correctly.
            with self.capture_on_commit_callbacks(execute=True):
                response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 202
        response = self.client.get(self.get_rollback_endpoint())

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["status"] == JobStatus.COMPLETE
        entry.refresh_from_db()
        assert entry.title == "Before"
        assert snapshot_entry(entry) == original_state

    @pytest.mark.parametrize(
        "status",
        [UpdateJobStatus.FAILED, UpdateJobStatus.STARTED, UpdateJobStatus.ROLLED_BACK],
    )
    def test_only_completed_jobs_can_be_rolled_back(self, status):
        self.job.status = status
        self.job.save()

        response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 400
        assert not RollbackJob.objects.exists()

    def test_job_without_snapshot_cannot_be_rolled_back(self):
        self.job.change_snapshot = None
        self.job.save()

        response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 400
        assert not RollbackJob.objects.exists()

    def test_job_without_expiry_cannot_be_rolled_back(self):
        self.job.rollback_expires_at = None
        self.job.save()

        response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 400
        assert not RollbackJob.objects.exists()

    def test_request_two_days_after_expiry_is_rejected(self):
        self.job.rollback_expires_at = timezone.now() - timedelta(days=2)
        self.job.save()

        response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data == ["The seven-day rollback window has expired."]
        assert not RollbackJob.objects.filter(update_job=self.job).exists()

    @pytest.mark.parametrize(
        "status", [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE]
    )
    def test_duplicate_request_rejected(self, status):
        factories.RollbackJobFactory(update_job=self.job, status=status)

        response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 400
        assert RollbackJob.objects.count() == 1

    def test_failed_rollback_can_be_requested_again(self):
        rollback_job = factories.RollbackJobFactory(
            update_job=self.job,
            status=JobStatus.FAILED,
            message="Previous error",
            task_id="previous-task",
            conflicts=[{"id": "previous-entry", "fields": ["title"]}],
            last_modified_by=factories.UserFactory(),
        )
        original_creator = rollback_job.created_by

        response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 202
        response_data = json.loads(response.content)
        assert response_data["id"] == str(rollback_job.id)

        rollback_job.refresh_from_db()
        assert rollback_job.status == JobStatus.ACCEPTED
        assert rollback_job.message is None
        assert rollback_job.task_id is None
        assert rollback_job.conflicts == []
        assert rollback_job.created_by == original_creator
        assert rollback_job.last_modified_by == self.user
        assert RollbackJob.objects.count() == 1

    def test_active_import_blocks_rollback(self):
        factories.ImportJobFactory(site=self.site, status=JobStatus.ACCEPTED)

        response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 400
        self.job.refresh_from_db()
        assert self.job.status == UpdateJobStatus.COMPLETE
        assert not RollbackJob.objects.exists()

    def test_active_update_validation_blocks_rollback(self):
        factories.UpdateJobFactory(site=self.site, validation_status=JobStatus.STARTED)

        response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 400
        self.job.refresh_from_db()
        assert self.job.status == UpdateJobStatus.COMPLETE
        assert not RollbackJob.objects.exists()

    def test_active_rollback_blocks_another_rollback(self):
        factories.RollbackJobFactory(
            update_job=factories.UpdateJobFactory(site=self.site),
            status=JobStatus.ACCEPTED,
        )

        response = self.client.post(self.get_rollback_endpoint())

        assert response.status_code == 400
        self.job.refresh_from_db()
        assert self.job.status == UpdateJobStatus.COMPLETE
        assert not RollbackJob.objects.filter(update_job=self.job).exists()

    @pytest.mark.parametrize(
        "job_factory, endpoint",
        [
            (factories.ImportJobFactory, "api:importjob"),
            (factories.UpdateJobFactory, "api:updatejob"),
        ],
    )
    @pytest.mark.parametrize("action", ["confirm", "validate"])
    def test_active_rollback_blocks_import_and_update(
        self, job_factory, endpoint, action
    ):
        factories.RollbackJobFactory(update_job=self.job)
        job = job_factory(site=self.site, validation_status=JobStatus.COMPLETE)
        url = reverse(f"{endpoint}-{action}", args=[self.site.slug, job.id])

        response = self.client.post(url)

        assert response.status_code == 400

    @pytest.mark.parametrize("action", ["confirm", "validate", "notify"])
    def test_rolled_back_job_cannot_be_confirmed_validated_or_notified(self, action):
        self.job.status = UpdateJobStatus.ROLLED_BACK
        self.job.save()
        url = reverse(f"api:updatejob-{action}", args=[self.site.slug, self.job.id])

        response = self.client.post(url)

        assert response.status_code == 400
        self.job.refresh_from_db()
        assert self.job.status == UpdateJobStatus.ROLLED_BACK

    def test_rolled_back_job_cannot_be_deleted(self):
        self.job.status = UpdateJobStatus.ROLLED_BACK
        self.job.save()
        url = reverse("api:updatejob-detail", args=[self.site.slug, self.job.id])

        delete_response = self.client.delete(url)
        get_response = self.client.get(url)

        assert delete_response.status_code == 400
        assert get_response.status_code == 200
        response_data = json.loads(get_response.content)
        assert response_data["status"] == "rolled back"

    def test_missing_rollback_returns_404(self):
        response = self.client.get(self.get_rollback_endpoint())

        assert response.status_code == 404
