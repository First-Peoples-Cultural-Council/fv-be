import pytest

from backend.models.constants import Visibility
from backend.tests.factories import MTDExportJobFactory, SiteFactory


class TestMTDExportFormatModel:
    @pytest.mark.django_db
    def test_representation(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        mtd = MTDExportJobFactory(site=site)

        expected_str = f"{site.title} - MTD Export - {str(mtd.id)}"
        assert str(mtd) == expected_str
