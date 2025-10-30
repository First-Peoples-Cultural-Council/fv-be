import json

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.models.import_jobs import ImportJob, ImportJobMode
from backend.models.jobs import JobStatus
from backend.tests import factories
from backend.tests.factories.import_job_factories import ImportJobFactory
from backend.tests.test_apis.base.base_async_api_test import (
    AsyncWorkflowTestMixin,
    BaseAsyncSiteContentApiTest,
)
from backend.tests.test_apis.base.base_media_test import FormDataMixin
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestImportEndpoints(
    AsyncWorkflowTestMixin, FormDataMixin, BaseAsyncSiteContentApiTest
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
        standard_fields = self.get_expected_entry_standard_fields(instance, site)
        return {
            **standard_fields,
            "runAsUser": instance.run_as_user,
            "data": self.get_file_data(instance.data),
            "mode": instance.mode.lower(),
            "taskId": instance.task_id,
            "status": instance.status,
            "message": instance.message,
            "validationTaskId": instance.task_id,
            "validationStatus": instance.validation_status,
            "validationReport": instance.validation_report,
            "failedRowsCsv": instance.failed_rows_csv,
        }

    def get_valid_data(self, site=None):
        return {
            "title": "Test Title",
            "data": get_sample_file("import_job/minimal.csv", "text/csv"),
            "mode": "skip_duplicates",
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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility, AppRole.SUPERADMIN
        )

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
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility, AppRole.SUPERADMIN
        )

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200

    def test_failed_rows_csv_field_exists(self):
        site, _ = factories.get_site_with_app_admin(self.client, Visibility.PUBLIC)

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

    @pytest.mark.parametrize(
        "job_status", [JobStatus.ACCEPTED, JobStatus.COMPLETE, JobStatus.STARTED]
    )
    def test_cannot_delete_successful_job(self, job_status):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.SUPERADMIN
        )
        job = factories.ImportJobFactory.create(site=site)
        job.status = job_status
        job.save()

        response = self.client.delete(
            self.get_detail_endpoint(key=self.get_lookup_key(job), site_slug=site.slug)
        )

        assert response.status_code == 400

        jobs = ImportJob.objects.filter(id=job.id)
        assert jobs.count() == 1

    @pytest.mark.parametrize("job_status", [JobStatus.ACCEPTED, JobStatus.STARTED])
    def test_cannot_delete_job_with_started_validation(self, job_status):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.SUPERADMIN
        )
        job = factories.ImportJobFactory.create(site=site)
        job.validation_status = job_status
        job.save()

        response = self.client.delete(
            self.get_detail_endpoint(key=self.get_lookup_key(job), site_slug=site.slug)
        )

        assert response.status_code == 400

        jobs = ImportJob.objects.filter(id=job.id)
        assert jobs.count() == 1

    def test_update_jobs_not_in_list(self):
        site, _ = factories.get_site_with_app_admin(
            self.client, visibility=Visibility.PUBLIC, role=AppRole.SUPERADMIN
        )
        import_job = factories.ImportJobFactory.create(
            site=site, mode=ImportJobMode.SKIP_DUPLICATES
        )
        update_job = factories.ImportJobFactory.create(
            site=site, mode=ImportJobMode.UPDATE
        )

        response = self.client.get(self.get_list_endpoint(site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 1

        returned_job_ids = [item["id"] for item in response_data["results"]]

        assert str(import_job.id) in returned_job_ids
        assert str(update_job.id) not in returned_job_ids
