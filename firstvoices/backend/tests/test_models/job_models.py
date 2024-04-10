import pytest

from backend.models.constants import Visibility
from backend.models.jobs import (
    BulkVisibilityJob,
    CustomOrderRecalculationResult,
    JobStatus,
)
from backend.tests.factories import SiteFactory


class TestCustomOrderRecalculationResultModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        test_entry = CustomOrderRecalculationResult.objects.create(
            site=site, latest_recalculation_result={}, task_id="abc123", is_preview=True
        )

        expected_str = f"{site.title} - {test_entry.latest_recalculation_date}"
        assert str(test_entry) == expected_str


class TestBulkVisibilityJobModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        test_entry = BulkVisibilityJob.objects.create(
            site=site,
            task_id="abc123",
            status=JobStatus.ACCEPTED,
            from_visibility=Visibility.PUBLIC,
            to_visibility=Visibility.PUBLIC,
        )

        expected_str = f"{site.title} - BulkVisibility - {test_entry.status}"
        assert str(test_entry) == expected_str
