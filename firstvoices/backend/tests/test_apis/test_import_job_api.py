import pytest

from backend.models.import_jobs import ImportJob
from backend.tests.factories.import_job_factories import ImportJobFactory
from backend.tests.test_apis.base_api_test import BaseControlledSiteContentApiTest


class TestImportEndpoints(BaseControlledSiteContentApiTest):
    """
    End-to-end tests that the /import endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:importjob-list"
    API_DETAIL_VIEW = "api:importjob-detail"
    model = ImportJob

    def create_minimal_instance(self, site, visibility=None):
        return ImportJobFactory.create(site=site)

    def get_expected_response(self, instance, site):
        return {
            "url": f"http://testserver{self.get_detail_endpoint(instance.id, instance.site.slug)}",
            "id": str(instance.id),
            "title": instance.title,
        }

    def get_valid_data(self, site=None):
        return {
            "title": "Cool new title",
        }

    def get_valid_data_with_nulls(self, site=None):
        return {}

    def add_expected_defaults(self, data):
        return {
            **data,
        }

    def assert_created_instance(self, pk, data):
        instance = ImportJob.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass

    @pytest.mark.django_db
    def test_detail_member_access(self):
        pass

    @pytest.mark.django_db
    def test_detail_team_access(self):
        pass
