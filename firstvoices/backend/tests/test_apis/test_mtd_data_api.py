import pytest
from mothertongues.config.models import LanguageConfiguration
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Visibility
from backend.tasks.mtd_export_tasks import build_index_and_calculate_scores
from backend.tests import factories


class TestMTDDataEndpoint:
    """
    Tests that check the mtd-data endpoint for correct formatting and behavior.
    """

    API_MTD_VIEW = "api:mtd-data-list"
    APP_NAME = "backend"

    client = None

    def get_mtd_endpoint(self, site_slug):
        return reverse(self.API_MTD_VIEW, current_app=self.APP_NAME, args=[site_slug])

    def setup_method(self):
        self.client = APIClient()
        self.user = factories.get_non_member_user()
        self.client.force_authenticate(user=self.user)
        self.basic_config = LanguageConfiguration()

    @staticmethod
    def get_expected_response(site, mtd_export_format):
        mtd_export_format.refresh_from_db()

        return {
            "created": mtd_export_format.created.astimezone().isoformat(),
            "last_modified": mtd_export_format.last_modified.astimezone().isoformat(),
            "id": str(mtd_export_format.id),
            "site": site.id,
            "status": mtd_export_format.status,
            "task_id": mtd_export_format.task_id,
            "message": mtd_export_format.message,
            "export_result": {
                "config": mtd_export_format.export_result["config"],
                "l1_index": mtd_export_format.export_result["l1_index"],
                "l2_index": mtd_export_format.export_result["l2_index"],
                "data": mtd_export_format.export_result["data"],
            },
        }

    @pytest.mark.django_db
    def test_no_build_and_score(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        response = self.client.get(self.get_mtd_endpoint(site_slug=site.slug))
        assert response.status_code == 404
        assert (
            response.content
            == b"Site has not been indexed yet. MTD export format not found."
        )

    @pytest.mark.django_db
    def test_build_and_score(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.CharacterFactory.create_batch(10, site=site)
        factories.DictionaryEntryFactory.create_batch(
            10, site=site, visibility=Visibility.PUBLIC, translations=["translation"]
        )

        mtd = build_index_and_calculate_scores(site.slug)

        response = self.client.get(self.get_mtd_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        assert response.data == self.get_expected_response(site, mtd)
