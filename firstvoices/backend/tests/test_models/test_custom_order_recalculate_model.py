import pytest

from backend.models.async_results import CustomOrderRecalculationResult
from backend.models.constants import Visibility
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
