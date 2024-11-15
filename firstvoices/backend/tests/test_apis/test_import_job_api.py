import json

import pytest
from rest_framework.reverse import reverse

from backend.models.constants import AppRole, Role, Visibility
from backend.models.import_jobs import ImportJob, JobStatus
from backend.tests import factories
from backend.tests.factories.import_job_factories import ImportJobFactory
from backend.tests.test_apis.base_api_test import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    WriteApiTestMixin,
)
from backend.tests.test_apis.base_media_test import FormDataMixin
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestImportEndpoints(
    FormDataMixin,
    WriteApiTestMixin,
    SiteContentCreateApiTestMixin,
    BaseReadOnlyUncontrolledSiteContentApiTest,
):
    """
    End-to-end tests that the /import endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:importjob-list"
    API_DETAIL_VIEW = "api:importjob-detail"
    model = ImportJob

    def create_minimal_instance(self, site, visibility=None):
        return ImportJobFactory.create(site=site)

    def get_file_data(self, file):
        return {
            "path": f"http://testserver{file.content.url}",
            "mimetype": file.mimetype,
            "size": file.size,
        }

    def get_expected_response(self, instance, site):
        return {
            "id": str(instance.id),
            "url": f"http://testserver{self.get_detail_endpoint(instance.id, instance.site.slug)}",
            "title": instance.title,
            "runAsUser": instance.run_as_user,
            "data": self.get_file_data(instance.data),
            "created": instance.created.astimezone().isoformat(),
            "createdBy": instance.created_by.email,
            "lastModified": instance.last_modified.astimezone().isoformat(),
            "lastModifiedBy": instance.last_modified_by.email,
            "mode": instance.mode.lower(),
            "taskId": instance.task_id,
            "status": instance.status.lower(),
            "message": instance.message,
            "validationTaskId": instance.task_id,
            "validationStatus": instance.validation_status.lower(),
            "validationReport": instance.validation_report,
            "failedRowsCsv": instance.failed_rows_csv,
            "site": {
                "id": str(site.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}",
                "title": site.title,
                "slug": site.slug,
                "visibility": instance.site.get_visibility_display().lower(),
                "language": site.language.title,
            },
        }

    def get_valid_data(self, site=None):
        return {
            "title": "Test Title",
            "data": get_sample_file("import_job/minimal.csv", "text/csv"),
            "mode": "update",
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": "Test Title",
            "data": get_sample_file("import_job/minimal.csv", "text/csv"),
        }

    def get_valid_data_with_null_optional_charfields(self, site=None):
        pass

    def add_expected_defaults(self, data):
        return {
            **data,
        }

    def assert_created_instance(self, pk, data):
        instance = ImportJob.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        # To handle create_with_nulls_success_201
        if "mode" in expected_data:
            assert expected_data["mode"] == actual_response["mode"]
        assert actual_response["title"] == expected_data["title"]
        return self.assert_update_response(expected_data, actual_response)

    def assert_updated_instance(self, expected_data, actual_instance):
        if "mode" in expected_data:
            assert expected_data["mode"] == actual_instance.mode
        assert expected_data["title"] == actual_instance.title
        expected_file_name = expected_data["data"].file.name.split("/")[-1]
        actual_file_name = actual_instance.data.content.file.name.split("/")[-1]
        assert expected_file_name == actual_file_name

    def assert_update_response(self, expected_data, actual_response):
        expected_file_name = expected_data["data"].file.name.split("/")[-1]
        actual_file_name = actual_response["data"]["path"].split("/")[-1]
        assert expected_file_name == actual_file_name

    def test_invalid_dimensions(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file("import_job/invalid_dimensions.csv", "text/csv"),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data["data"] == [
            "CSV file has invalid dimensions. The size of a column or row doesn't fit the table dimensions."
        ]

    def test_required_headers_missing(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file(
                "import_job/required_headers_missing.csv", "text/csv"
            ),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data["data"] == [
            "CSV file does not have the all the required headers. Required headers are ['title', 'type']"
        ]

    def test_duplicate_headers(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file("import_job/duplicate_cols.csv", "text/csv"),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400

        response_data = json.loads(response.content)
        assert response_data["data"] == [
            "CSV file contains duplicate headers: title,type."
        ]

    def test_run_as_user_field_superadmins(self):
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        data = self.get_valid_data(site)
        data["run_as_user"] = user.email

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201
        response_data = json.loads(response.content)
        assert response_data["runAsUser"] == user.email

    def test_invalid_run_as_user_field(self):
        user = factories.get_app_admin(AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        data = self.get_valid_data(site)
        data["run_as_user"] = "abc@xyz.com"

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert response_data["runAsUser"] == ["Invalid email."]

    @pytest.mark.parametrize("role", [Role.EDITOR, Role.LANGUAGE_ADMIN])
    def test_run_as_user_field_non_superadmins_403(self, role):
        # run_as_user field can only be used by superadmins
        # return 400 if used by editors or language admins
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=role
        )

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)
        data["run_as_user"] = user.email

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 403
        response_data = json.loads(response.content)
        assert (
            response_data["detail"]
            == "You don't have permission to use the runAsUser field."
        )

    # Custom permissions tests
    @pytest.mark.skip("This endpoint has custom permissions.")
    def test_detail_team_access(self, role):
        # Only editor or above have access to this object
        # Check custom permissions tests below
        pass

    @pytest.mark.skip("This endpoint has custom permissions.")
    def test_detail_member_access(self, role):
        # Only editor or above have access to this object
        # Check custom permissions tests below
        pass

    @pytest.mark.skip(
        reason="Import job API does not have eligible optional charfields."
    )
    def test_create_with_null_optional_charfields_success_201(self):
        # Import job API does not have eligible optional charfields.
        pass

    @pytest.mark.skip(
        reason="Import job API does not have eligible optional charfields."
    )
    def test_update_with_null_optional_charfields_success_200(self):
        # Import job API does not have eligible optional charfields.
        pass

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT])
    @pytest.mark.parametrize("visibility", Visibility)
    def test_detail_403_for_members_and_assistants(self, role, visibility):
        site = factories.SiteFactory.create(visibility=visibility)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403

    @pytest.mark.parametrize("role", [Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.parametrize("visibility", Visibility)
    def test_detail_editor_and_language_admin_access(self, role, visibility):
        site = factories.SiteFactory.create(visibility=visibility)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    @pytest.mark.parametrize("visibility", Visibility)
    def test_detail_superadmin_access(self, visibility):
        site = self.create_site_with_app_admin(visibility, AppRole.SUPERADMIN)

        instance = self.create_minimal_instance(site=site)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT])
    def test_list_empty_for_non_admins(self, role):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        factories.JoinRequestFactory.create(site=site)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

    @pytest.mark.parametrize("role", [Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.parametrize("visibility", Visibility)
    def test_list_editor_and_language_admin_access(self, role, visibility):
        site = factories.SiteFactory.create(visibility=visibility)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200

    @pytest.mark.parametrize("visibility", Visibility)
    def test_list_app_admin_access(self, visibility):
        site = self.create_site_with_app_admin(visibility, AppRole.SUPERADMIN)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200

    def test_failed_rows_csv_field_exists(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file(
                "import_job/invalid_dictionary_entries.csv", "text/csv"
            ),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )
        response_data = json.loads(response.content)

        assert "failedRowsCsv" in response_data


class TestImportJobConfirmAction(TestImportEndpoints):
    API_CONFIRM_ACTION = "api:importjob-confirm"

    def test_confirm_action(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )

        self.client.force_authenticate(user=user)

        # Mock import-job with completed validation status
        file_content = get_sample_file("import_job/all_valid_columns.csv", "text/csv")
        file = factories.FileFactory(content=file_content)
        import_job_instance = ImportJobFactory(
            site=site, data=file, validation_status=JobStatus.COMPLETE
        )

        confirm_endpoint = reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[site.slug, str(import_job_instance.id)],
        )

        response = self.client.post(confirm_endpoint)

        assert response.status_code == 202
        response_data = json.loads(response.content)

        assert response_data["status"] == JobStatus.STARTED

    def test_confirm_action_404_unknown_key(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        confirm_endpoint = reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[site.slug, "fake-key"],
        )

        response = self.client.post(confirm_endpoint)

        assert response.status_code == 404


class TestImportJobValidateAction(TestImportEndpoints):
    API_VALIDATE_ACTION = "api:importjob-validate"

    @pytest.mark.django_db(transaction=True)
    def test_validate_action(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file("import_job/minimal.csv", "text/csv"),
        }

        # Initial run
        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )
        assert response.status_code == 201
        response_data = json.loads(response.content)

        import_job = ImportJob.objects.filter(id=response_data["id"])[0]
        old_validation_report_id = import_job.validation_report.id

        # Validate endpoint
        validate_endpoint = reverse(
            self.API_VALIDATE_ACTION,
            current_app=self.APP_NAME,
            args=[site.slug, str(import_job.id)],
        )
        response = self.client.post(validate_endpoint)
        assert response.status_code == 202

        import_job = ImportJob.objects.filter(id=response_data["id"])[0]
        new_validation_report_id = import_job.validation_report.id

        assert new_validation_report_id != old_validation_report_id
