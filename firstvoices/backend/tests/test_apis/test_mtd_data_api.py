import hashlib
from datetime import datetime

import pytest
from mothertongues.config.models import LanguageConfiguration
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models import MTDExportJob
from backend.models.constants import Role, Visibility
from backend.models.jobs import JobStatus
from backend.tasks.mtd_export_tasks import build_index_and_calculate_scores
from backend.tests import factories


class TestMTDDataEndpoint:
    """
    Tests that check the mtd-data endpoint for correct formatting and behavior.
    """

    API_MTD_VIEW = "api:mtd-data-list"
    APP_NAME = "backend"

    client = None
    content_type = "application/json"

    def get_mtd_endpoint(self, site_slug):
        return reverse(self.API_MTD_VIEW, current_app=self.APP_NAME, args=[site_slug])

    def setup_method(self):
        self.client = APIClient()
        self.user = factories.get_non_member_user()
        self.client.force_authenticate(user=self.user)
        self.basic_config = LanguageConfiguration()

    @staticmethod
    def get_expected_mtd_data_response(mtd):
        return {
            "data": mtd["data"],
            "config": mtd["config"],
            "l1_index": mtd["l1_index"],
            "l2_index": mtd["l2_index"],
        }

    @staticmethod
    def get_expected_task_response(site, mtd_export_format):
        mtd_export_format.refresh_from_db()

        return {
            "created": mtd_export_format.created.astimezone().isoformat(),
            "last_modified": mtd_export_format.last_modified.astimezone().isoformat(),
            "id": str(mtd_export_format.id),
            "site": site.id,
            "status": mtd_export_format.status,
            "task_id": mtd_export_format.task_id,
            "message": mtd_export_format.message,
        }

    @pytest.mark.django_db
    def test_no_build_and_score(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        response = self.client.get(self.get_mtd_endpoint(site_slug=site.slug))
        assert response.status_code == 404
        assert (
            response.content
            == b'{"message":"Site has not been successfully indexed yet. MTD export format not found."}'
        )

    @pytest.mark.django_db
    def test_build_and_score(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.CharacterFactory.create_batch(10, site=site)
        factories.DictionaryEntryFactory.create_batch(
            10, site=site, visibility=Visibility.PUBLIC, translations=["translation"]
        )

        mtd = MTDExportJob.objects.get(id=build_index_and_calculate_scores(site.slug))

        response = self.client.get(self.get_mtd_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        assert response.data == self.get_expected_mtd_data_response(mtd.export_result)

        response = self.client.get(
            self.get_mtd_endpoint(site_slug=site.slug) + "/task/"
        )
        assert response.status_code == 404
        assert (
            response.content
            == b'{"message":"MTD export task information not available."}'
        )

    @pytest.mark.django_db
    def test_build_and_score_task_superadmin(self):
        self.user = factories.get_superadmin()
        self.client.force_authenticate(user=self.user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.CharacterFactory.create_batch(10, site=site)
        factories.DictionaryEntryFactory.create_batch(
            10, site=site, visibility=Visibility.PUBLIC, translations=["translation"]
        )

        mtd = MTDExportJob.objects.get(id=build_index_and_calculate_scores(site.slug))

        response = self.client.get(
            self.get_mtd_endpoint(site_slug=site.slug) + "/task/"
        )
        assert response.status_code == 200
        assert response.data[0] == self.get_expected_task_response(site, mtd)

    @pytest.mark.django_db
    @pytest.mark.parametrize("status", [JobStatus.CANCELLED, JobStatus.FAILED])
    def test_data_integrity_build_and_score_failed(self, status):
        self.user = factories.get_superadmin()
        self.client.force_authenticate(user=self.user)

        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.CharacterFactory.create_batch(10, site=site)
        factories.DictionaryEntryFactory.create_batch(
            10, site=site, visibility=Visibility.PUBLIC, translations=["translation"]
        )

        mtd = MTDExportJob.objects.get(id=build_index_and_calculate_scores(site.slug))

        factories.MTDExportJobFactory.create(site=site, status=status)

        response = self.client.get(self.get_mtd_endpoint(site_slug=site.slug))
        assert response.status_code == 200
        assert response.data == self.get_expected_mtd_data_response(mtd.export_result)

        response = self.client.get(
            self.get_mtd_endpoint(site_slug=site.slug) + "/task/"
        )
        assert response.status_code == 200
        assert response.data[0]["status"] == status

    @pytest.mark.django_db
    def test_etag_and_last_modified(self):
        site, _ = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        factories.CharacterFactory.create_batch(10, site=site)
        factories.DictionaryEntryFactory.create_batch(
            10, site=site, visibility=Visibility.PUBLIC, translations=["translation"]
        )

        mtd = MTDExportJob.objects.get(id=build_index_and_calculate_scores(site.slug))
        url = self.get_mtd_endpoint(site_slug=site.slug)

        response = self.client.get(url)

        expected_etag = hashlib.md5(
            ":".join(str(mtd.system_last_modified)).encode("utf-8")
        ).hexdigest()
        assert response.status_code == 200
        assert response["ETag"].strip('"') == expected_etag

        date_string = response["Last-Modified"]
        format_string = "%a, %d %b %Y %H:%M:%S %Z"
        last_modified_header = datetime.strptime(date_string, format_string)

        assert last_modified_header.strftime(
            "%Y-%m-%d %H:%M:%S"
        ) == mtd.system_last_modified.strftime("%Y-%m-%d %H:%M:%S")
