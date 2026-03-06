import pytest
from django.core.exceptions import ValidationError

from backend.models.constants import Role
from backend.models.jobs import JobStatus
from backend.tests import factories


@pytest.mark.django_db
class TestExportJobModel:

    def setup_method(self):
        self.site = factories.SiteFactory()
        self.user = factories.UserFactory()
        factories.MembershipFactory.create(
            user=self.user, site=self.site, role=Role.LANGUAGE_ADMIN
        )

    @pytest.mark.parametrize(
        "job_status", [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.COMPLETE]
    )
    def test_started_and_complete_jobs_cannot_exceed_limit(self, job_status):
        factories.ExportJobFactory.create_batch(
            10, created_by=self.user, site=self.site, status=job_status
        )

        with pytest.raises(ValidationError) as e:
            factories.ExportJobFactory.create(
                created_by=self.user, site=self.site, status=job_status
            )

        assert str(e.value.messages[0]) == (
            "You have reached the maximum number of simultaneous export jobs (10). "
            "Please delete completed jobs that you no longer need to allow new export jobs to be created."
        )
