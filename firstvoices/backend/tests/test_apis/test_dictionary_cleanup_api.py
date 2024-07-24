import json

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.models.jobs import DictionaryCleanupJob, JobStatus
from backend.tasks.dictionary_cleanup_tasks import cleanup_dictionary
from backend.tests import factories
from backend.tests.test_apis.base_api_test import (
    BaseReadOnlyUncontrolledSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    SuperAdminAsyncJobPermissionsMixin,
    WriteApiTestMixin,
)
from backend.tests.test_search_indexing.base_indexing_tests import (
    TransactionOnCommitMixin,
)


class TestDictionaryCleanupAPI(
    WriteApiTestMixin,
    SiteContentCreateApiTestMixin,
    TransactionOnCommitMixin,
    SuperAdminAsyncJobPermissionsMixin,
    BaseReadOnlyUncontrolledSiteContentApiTest,
):
    API_LIST_VIEW = "api:dictionary-cleanup-list"
    API_DETAIL_VIEW = "api:dictionary-cleanup-detail"
    CLEAR = "/clear"

    model = DictionaryCleanupJob

    @pytest.fixture(scope="function")
    def mock_dictionary_cleanup_task(self, mocker):
        self.mocked_func = mocker.patch(
            "backend.tasks.dictionary_cleanup_tasks.cleanup_dictionary.apply_async"
        )

    def create_minimal_instance(self, site, visibility):
        return factories.DictionaryCleanupJobFactory.create(site=site, is_preview=False)

    def get_expected_detail_response(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        return {
            **standard_fields,
            "status": instance.get_status_display().lower(),
            "taskId": instance.task_id,
            "message": instance.message,
            "cleanupResult": {"unknownCharacterCount": 0, "updatedEntries": []},
            "isPreview": instance.is_preview,
        }

    def get_expected_response(self, instance, site):
        return self.get_expected_detail_response(instance, site)

    def get_valid_data(self, site=None):
        return {}

    def assert_created_instance(self, pk, data):
        instance = DictionaryCleanupJob.objects.get(pk=pk)
        return self.get_expected_response(instance, instance.site)

    def assert_created_response(self, expected_data, actual_response):
        assert actual_response == expected_data

    @pytest.mark.skip(
        reason="Dictionary cleanup jobs can only be accessed by superusers."
    )
    def test_detail_member_access(self, role):
        # Dictionary cleanup jobs can only be accessed by superusers.
        pass

    @pytest.mark.skip(
        reason="Dictionary cleanup jobs can only be accessed by superusers."
    )
    def test_detail_team_access(self, role):
        # Dictionary cleanup jobs can only be accessed by superusers.
        pass

    @pytest.mark.skip(reason="Dictionary cleanup jobs have no eligible nulls.")
    def test_create_with_nulls_success_201(self):
        # Dictionary cleanup jobs have no eligible nulls.
        pass

    @pytest.mark.skip(reason="Dictionary cleanup jobs require no data to post.")
    def test_create_invalid_400(self):
        # Dictionary cleanup jobs require no data to post.
        pass

    @pytest.mark.django_db
    def test_list_minimal(self):
        site = factories.SiteFactory.create()
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_list_response_item(
            instance, site
        )

    @pytest.mark.django_db
    def test_detail_minimal(self):
        site = factories.SiteFactory.create()
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data == self.get_expected_detail_response(instance, site)

    @pytest.mark.django_db
    def test_create_success_201(self):
        site = self.create_site_with_app_admin(Visibility.PUBLIC)

        data = self.get_valid_data(site)

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

        response_data = json.loads(response.content)
        pk = response_data["id"]

        self.assert_created_instance(pk, data)
        assert response_data == self.get_expected_response(
            DictionaryCleanupJob.objects.get(pk=pk), site
        )

    @pytest.mark.django_db
    def test_recalculate_result_display(self, result="cleanupResult"):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        alphabet = factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        factories.DictionaryEntryFactory.create(site=site, title="tèst")
        factories.DictionaryEntryFactory.create(site=site, title="ᐱᐱᐱ")
        factories.CharacterFactory.create(site=site, title="t")
        factories.CharacterFactory.create(site=site, title="e")
        factories.CharacterFactory.create(site=site, title="s")
        factories.CharacterFactory.create(site=site, title="A")
        alphabet.input_to_canonical_map = [
            {"in": "è", "out": "e"},
            {"in": "ᐱ", "out": "A"},
        ]
        alphabet.save()

        job = self.create_minimal_instance(site=site, visibility=None)
        cleanup_dictionary(job.id)
        job.refresh_from_db()

        assert job.status == JobStatus.COMPLETE

        response = self.client.get(
            self.get_detail_endpoint(key=job.id, site_slug=site.slug)
        )
        response_data = json.loads(response.content)
        assert response.status_code == 200
        assert response_data[result] == {
            "unknownCharacterCount": {},
            "updatedEntries": [
                {
                    "title": "tèst",
                    "cleanedTitle": "test",
                    "isTitleUpdated": True,
                    "previousCustomOrder": "⚑t⚑è⚑s⚑t",
                    "newCustomOrder": "!#$!",
                },
                {
                    "title": "ᐱᐱᐱ",
                    "cleanedTitle": "AAA",
                    "isTitleUpdated": True,
                    "previousCustomOrder": "⚑ᐱ⚑ᐱ⚑ᐱ",
                    "newCustomOrder": "%%%",
                },
            ],
        }

    @pytest.mark.django_db
    def test_clear(self, is_preview=False):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        factories.DictionaryCleanupJobFactory.create(
            site=site, is_preview=is_preview, status=JobStatus.COMPLETE
        )
        factories.DictionaryCleanupJobFactory.create(
            site=site, is_preview=is_preview, status=JobStatus.FAILED
        )
        factories.DictionaryCleanupJobFactory.create(
            site=site, is_preview=is_preview, status=JobStatus.CANCELLED
        )

        response_delete = self.client.delete(
            self.get_list_endpoint(site.slug) + self.CLEAR
        )
        assert response_delete.status_code == 204

        response_get = self.client.get(self.get_list_endpoint(site.slug))
        response_get_data = json.loads(response_get.content)
        assert response_get.status_code == 200
        assert response_get_data["results"] == []

    @pytest.mark.django_db
    def test_clear_403_non_member(self):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        self.client.force_authenticate(user=user)

        response = self.client.delete(self.get_list_endpoint(site.slug) + self.CLEAR)
        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "role",
        [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    def test_clear_403_non_superuser(self, role):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        factories.MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        response = self.client.delete(self.get_list_endpoint(site.slug) + self.CLEAR)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_clear_403_staff(self):
        site = factories.SiteFactory.create()
        user = factories.UserFactory.create()
        factories.AppMembershipFactory.create(user=user, role=AppRole.STAFF)
        self.client.force_authenticate(user=user)

        response = self.client.delete(self.get_list_endpoint(site.slug) + self.CLEAR)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_dictionary_cleanup_called(self, mock_dictionary_cleanup_task):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        with self.capture_on_commit_callbacks(execute=True):
            response = self.client.post(
                self.get_list_endpoint(site_slug=site.slug),
                data={},
                content_type=self.content_type,
            )

        assert response.status_code == 201
        assert self.mocked_func.call_count == 1


class TestDictionaryCleanupPreviewAPI(TestDictionaryCleanupAPI):
    API_LIST_VIEW = "api:dictionary-cleanup-preview-list"
    API_DETAIL_VIEW = "api:dictionary-cleanup-preview-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.DictionaryCleanupJobFactory.create(site=site, is_preview=True)

    def get_expected_detail_response(self, instance, site):
        standard_fields = self.get_expected_standard_fields(instance, site)
        return {
            **standard_fields,
            "status": instance.get_status_display().lower(),
            "taskId": instance.task_id,
            "message": instance.message,
            "cleanupPreviewResult": None,
            "isPreview": instance.is_preview,
        }

    @pytest.mark.django_db
    def test_recalculate_result_display(self, result="cleanupPreviewResult"):
        super().test_recalculate_result_display(result=result)

    @pytest.mark.django_db
    def test_clear(self, is_preview=True):
        super().test_clear(is_preview=is_preview)
