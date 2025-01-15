import json
from unittest.mock import MagicMock, patch

import pytest
from django.utils.http import urlencode
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import AppRole, Role, Visibility
from backend.models.import_jobs import ImportJob, JobStatus
from backend.tests import factories
from backend.tests.factories.import_job_factories import ImportJobFactory
from backend.tests.test_apis.base_api_test import (
    BaseApiTest,
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
        # No optional char field
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

    @pytest.mark.parametrize(
        "filename",
        [
            "ascii.csv",
            "windows1252.csv",
            "MacRoman.csv",
            "utf8.csv",
            "iso8859.csv",
        ],
    )
    def test_csv_with_valid_encodings_accepted(self, filename):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file(f"import_job/encodings/{filename}", "text/csv"),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

    def test_csv_with_invalid_encodings_not_accepted(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file("import_job/encodings/utf32.csv", "text/csv"),
        }

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            "File encoding must be of supported type. - Encoding: [UTF-32]. Supported encodings: "
            "['utf-8-sig', 'ascii', 'iso-8859-1', 'windows-1252', 'macroman']."
            in response_data["data"]
        )

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


@pytest.mark.django_db(transaction=True)
class TestImportJobConfirmAction(BaseApiTest):
    API_CONFIRM_ACTION = "api:importjob-confirm"

    def create_minimal_instance(self, visibility):
        # Not required for this endpoint
        return {}

    def get_expected_response(self, instance):
        # Not required for this endpoint
        return {}

    def setup_method(self):
        self.client = APIClient()
        self.site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=user)

        file_content = get_sample_file("import_job/all_valid_columns.csv", "text/csv")
        file = factories.FileFactory(content=file_content)
        self.import_job_instance = ImportJobFactory(
            site=self.site, data=file, validation_status=JobStatus.COMPLETE
        )

    def test_confirm_action(self):
        confirm_endpoint = reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(self.import_job_instance.id)],
        )

        response = self.client.post(confirm_endpoint)

        assert response.status_code == 202
        response_data = json.loads(response.content)

        assert response_data["status"] == JobStatus.STARTED

    def test_more_than_one_jobs_not_allowed(self):
        import_job_instance = ImportJobFactory(
            site=self.site,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.STARTED,
        )

        confirm_endpoint = reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(import_job_instance.id)],
        )
        response = self.client.post(confirm_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert (
            "There is at least 1 job on this site that is already running or queued to run soon. Please wait for "
            "it to finish before starting a new one." in response
        )

    @pytest.mark.parametrize("status", [JobStatus.COMPLETE, JobStatus.FAILED])
    def test_reconfirming_a_completed_job_not_allowed(self, status):
        import_job_instance = ImportJobFactory(
            site=self.site,
            validation_status=JobStatus.COMPLETE,
            status=status,
        )

        confirm_endpoint = reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(import_job_instance.id)],
        )
        response = self.client.post(confirm_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert (
            "The job has already been executed once. "
            "Please create another batch request to import the entries." in response
        )

    @pytest.mark.parametrize(
        "validation_status",
        [JobStatus.ACCEPTED, JobStatus.STARTED, JobStatus.FAILED, JobStatus.CANCELLED],
    )
    def test_confirm_only_allowed_for_completed_dry_run(self, validation_status):
        import_job_instance = ImportJobFactory(
            site=self.site,
            validation_status=validation_status,
        )

        confirm_endpoint = reverse(
            self.API_CONFIRM_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(import_job_instance.id)],
        )
        response = self.client.post(confirm_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert (
            "A successful dry-run is required before doing the import. "
            "Please fix any issues found during the dry-run of the CSV file and run a new batch."
            in response
        )


class TestImportJobValidateAction(FormDataMixin, BaseApiTest):
    API_LIST_VIEW = "api:importjob-list"
    API_VALIDATE_ACTION = "api:importjob-validate"

    def create_minimal_instance(self, visibility):
        # Not required for this endpoint
        return {}

    def get_expected_response(self, instance):
        # Not required for this endpoint
        return {}

    def get_list_endpoint(self, site_slug=None, query_kwargs=None):
        """
        query_kwargs accept query parameters e.g. query_kwargs={"contains": "WORD"}
        """
        url = reverse(self.API_LIST_VIEW, current_app=self.APP_NAME, args=[site_slug])
        if query_kwargs:
            return f"{url}?{urlencode(query_kwargs)}"
        return url

    def setup_method(self):
        super().setup_method()

        user = factories.UserFactory.create()
        factories.AppMembershipFactory.create(user=user, role=AppRole.SUPERADMIN)

        self.client.force_authenticate(user=user)
        self.site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        data = {
            "title": "Test Title",
            "data": get_sample_file("import_job/minimal.csv", "text/csv"),
        }

        # Initial run
        response = self.client.post(
            self.get_list_endpoint(site_slug=self.site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )
        assert response.status_code == 201
        response_data = json.loads(response.content)

        self.import_job = ImportJob.objects.filter(id=response_data["id"])[0]

    @pytest.mark.django_db(transaction=True)
    def test_exception_fetching_previous_report(self, caplog):
        # Simulating a general exception when fetching/deleting a previous
        # validation report

        mock_report = MagicMock()
        mock_report.delete.side_effect = Exception("General Exception")
        with patch(
            "backend.tasks.import_job_tasks.ImportJobReport.objects.filter",
            return_value=mock_report,
        ):
            validate_endpoint = reverse(
                self.API_VALIDATE_ACTION,
                current_app=self.APP_NAME,
                args=[self.site.slug, str(self.import_job.id)],
            )

            response = self.client.post(validate_endpoint)

        # Updating import-job instance in memory
        import_job = ImportJob.objects.filter(id=self.import_job.id).first()

        assert response.status_code == 202

        assert "General Exception" in caplog.text
        assert import_job.validation_status == JobStatus.FAILED

    @pytest.mark.django_db(transaction=True)
    def test_validate_action(self):
        old_validation_report_id = self.import_job.validation_report.id

        validate_endpoint = reverse(
            self.API_VALIDATE_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(self.import_job.id)],
        )
        response = self.client.post(validate_endpoint)
        assert response.status_code == 202

        import_job = ImportJob.objects.filter(id=self.import_job.id)[0]
        new_validation_report_id = import_job.validation_report.id

        assert new_validation_report_id != old_validation_report_id

    @pytest.mark.django_db(transaction=True)
    def test_more_than_one_jobs_not_allowed(self):
        ImportJobFactory(
            site=self.site,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.STARTED,
        )  # second job

        validate_endpoint = reverse(
            self.API_VALIDATE_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(self.import_job.id)],
        )
        response = self.client.post(validate_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert (
            "There is at least 1 job on this site that is already running or queued to run soon. Please wait for "
            "it to finish before starting a new one." in response
        )

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize(
        "validation_status", [JobStatus.ACCEPTED, JobStatus.ACCEPTED]
    )
    def test_validating_current_job_again_not_allowed(self, validation_status):
        # removing the job created in setup method
        ImportJob.objects.filter(id=self.import_job.id).delete()

        import_job = ImportJobFactory(
            site=self.site,
            validation_status=validation_status,
        )

        # Validate endpoint
        validate_endpoint = reverse(
            self.API_VALIDATE_ACTION,
            current_app=self.APP_NAME,
            args=[self.site.slug, str(import_job.id)],
        )

        response = self.client.post(validate_endpoint)
        assert response.status_code == 400

        response = json.loads(response.content)
        assert (
            "The specified job is already running or queued. "
            "Please wait for it to finish before starting a new one." in response
        )
