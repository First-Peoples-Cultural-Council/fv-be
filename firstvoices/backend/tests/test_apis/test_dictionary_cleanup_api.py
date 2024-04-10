import json
from unittest.mock import ANY, patch

import pytest
from django.urls import reverse

from backend.models import DictionaryEntry
from backend.models.constants import AppRole, Role, Visibility
from backend.serializers.job_serializers import CustomOrderRecalculationResultSerializer
from backend.tasks.alphabet_tasks import (
    recalculate_custom_order,
    recalculate_custom_order_preview,
)
from backend.tests import factories
from backend.tests.test_apis.base_api_test import BaseApiTest


class TestDictionaryCleanupPreviewAPI(BaseApiTest):
    API_DETAIL_VIEW = "api:dictionary-cleanup-preview-list"
    SUCCESS_MESSAGE = {"message": "Recalculation preview has been queued."}
    CLEAR = "/clear"

    @pytest.fixture
    def mock_celery_task_status(self, mocker):
        with patch.object(
            CustomOrderRecalculationResultSerializer, "get_current_task_status"
        ) as mock_method:
            yield mock_method

    @pytest.fixture
    def mock_celery_task_response_preview(self, mocker):
        with patch(
            "backend.views.custom_order_recalculate_views.recalculate_custom_order_preview"
        ) as mock_method:
            yield mock_method

    def get_detail_endpoint(self, site_slug):
        return reverse(
            self.API_DETAIL_VIEW, current_app=self.APP_NAME, args=[site_slug]
        )

    def get_expected_response(self, site):
        return [
            {
                "site": site.title,
                "currentPreviewTaskStatus": "SUCCESS",
                "latestRecalculationPreviewDate": ANY,
                "latestRecalculationPreviewResult": {
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
                },
            }
        ]

    @pytest.mark.django_db
    def test_recalculate_get_404(self):
        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_detail_endpoint("missing-slug"))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_recalculate_post_404(self):
        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_detail_endpoint("missing-slug"))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_recalculate_post_403(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_detail_endpoint(site.slug))
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_recalculate_get_empty(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_detail_endpoint(site.slug))
        response_data = json.loads(response.content)
        assert response.status_code == 200
        assert response_data["results"] == []

    @pytest.mark.django_db
    def test_recalculate_post_success(self, mock_celery_task_response_preview):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        factories.DictionaryEntryFactory.create(site=site, title="test")

        mock_celery_task_response_preview.return_value = None

        response = self.client.post(self.get_detail_endpoint(site.slug))

        response_data = json.loads(response.content)
        assert response.status_code == 202
        assert response_data == self.SUCCESS_MESSAGE

    @pytest.mark.django_db
    def test_recalculate_result_display(self, mock_celery_task_status):
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

        recalculate_custom_order_preview(site_slug=site.slug)
        mock_celery_task_status.return_value = "SUCCESS"

        response = self.client.get(self.get_detail_endpoint(site.slug))
        response_data = json.loads(response.content)
        assert response.status_code == 200
        assert response_data["results"] == self.get_expected_response(site=site)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "role",
        (
            Role.MEMBER,
            Role.ASSISTANT,
            Role.EDITOR,
            Role.LANGUAGE_ADMIN,
        ),
    )
    def test_recalculate_permissions_403_user_roles(
        self, mock_celery_task_response_preview, role
    ):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=role
        )
        self.client.force_authenticate(user=user)

        mock_celery_task_response_preview.return_value = None

        response = self.client.get(self.get_detail_endpoint(site.slug))

        assert response.status_code == 403

        response = self.client.post(self.get_detail_endpoint(site.slug))

        assert response.status_code == 403

        response = self.client.delete(self.get_detail_endpoint(site.slug) + self.CLEAR)

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_recalculate_permissions_403_staff(self, mock_celery_task_response_preview):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.STAFF)
        self.client.force_authenticate(user=user)

        mock_celery_task_response_preview.return_value = None

        response = self.client.get(self.get_detail_endpoint(site.slug))

        assert response.status_code == 403

        response = self.client.post(self.get_detail_endpoint(site.slug))

        assert response.status_code == 403

        response = self.client.delete(self.get_detail_endpoint(site.slug) + self.CLEAR)

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_recaltulate_permissions_superadmin(
        self, mock_celery_task_response_preview
    ):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        mock_celery_task_response_preview.return_value = None

        response = self.client.get(self.get_detail_endpoint(site.slug))

        assert response.status_code == 200

        response = self.client.post(self.get_detail_endpoint(site.slug))

        assert response.status_code == 202

        response = self.client.delete(self.get_detail_endpoint(site.slug) + self.CLEAR)

        assert response.status_code == 204

    @pytest.mark.django_db
    def test_clear(self, is_preview=True):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        factories.CustomOrderRecalculationResultFactory.create(
            site=site, is_preview=is_preview
        )

        response_delete = self.client.delete(
            self.get_detail_endpoint(site.slug) + self.CLEAR
        )
        assert response_delete.status_code == 204

        response_get = self.client.get(self.get_detail_endpoint(site.slug))
        response_get_data = json.loads(response_get.content)
        assert response_get.status_code == 200
        assert response_get_data["results"] == []

    @pytest.mark.django_db
    def test_clear_403(self, is_preview=True):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        factories.CustomOrderRecalculationResultFactory.create(
            site=site, is_preview=is_preview
        )

        response_delete = self.client.delete(
            self.get_detail_endpoint(site.slug) + self.CLEAR
        )
        assert response_delete.status_code == 403


class TestDictionaryCleanupAPI(TestDictionaryCleanupPreviewAPI):
    API_DETAIL_VIEW = "api:dictionary-cleanup-list"
    SUCCESS_MESSAGE = {"message": "Recalculation has been queued."}

    @pytest.fixture
    def mock_celery_task_response(self, mocker):
        with patch(
            "backend.views.custom_order_recalculate_views.recalculate_custom_order"
        ) as mock_method:
            yield mock_method

    def get_expected_response(self, site):
        response = super().get_expected_response(site=site)
        response[0]["currentTaskStatus"] = response[0].pop("currentPreviewTaskStatus")
        response[0]["latestRecalculationDate"] = response[0].pop(
            "latestRecalculationPreviewDate"
        )
        response[0]["latestRecalculationResult"] = response[0].pop(
            "latestRecalculationPreviewResult"
        )
        return response

    @pytest.mark.django_db
    def test_recalculate_result_display(self, mock_celery_task_status):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        alphabet = factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        entry1 = factories.DictionaryEntryFactory.create(site=site, title="tèst")
        entry2 = factories.DictionaryEntryFactory.create(site=site, title="ᐱᐱᐱ")
        factories.CharacterFactory.create(site=site, title="t")
        factories.CharacterFactory.create(site=site, title="e")
        factories.CharacterFactory.create(site=site, title="s")
        factories.CharacterFactory.create(site=site, title="A")
        alphabet.input_to_canonical_map = [
            {"in": "è", "out": "e"},
            {"in": "ᐱ", "out": "A"},
        ]
        alphabet.save()

        recalculate_custom_order(site_slug=site.slug)
        mock_celery_task_status.return_value = "SUCCESS"

        response = self.client.get(self.get_detail_endpoint(site.slug))
        response_data = json.loads(response.content)
        assert response.status_code == 200
        assert response_data["results"] == self.get_expected_response(site=site)

        updated_entry1 = DictionaryEntry.objects.get(id=entry1.id)
        updated_entry2 = DictionaryEntry.objects.get(id=entry2.id)
        assert updated_entry1.title == "test"
        assert updated_entry1.custom_order == "!#$!"
        assert updated_entry2.title == "AAA"
        assert updated_entry2.custom_order == "%%%"

    @pytest.mark.django_db
    def test_recalculate_post_success(self, mock_celery_task_response):
        super().test_recalculate_post_success(mock_celery_task_response)

    @pytest.mark.django_db
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "role",
        (
            Role.MEMBER,
            Role.ASSISTANT,
            Role.EDITOR,
            Role.LANGUAGE_ADMIN,
        ),
    )
    def test_recalculate_permissions_403_user_roles(
        self, mock_celery_task_response, role
    ):
        super().test_recalculate_permissions_403_user_roles(
            mock_celery_task_response, role
        )

    @pytest.mark.django_db
    def test_recalculate_permissions_403_staff(self, mock_celery_task_response):
        super().test_recalculate_permissions_403_staff(mock_celery_task_response)

    @pytest.mark.django_db
    def test_recaltulate_permissions_superadmin(self, mock_celery_task_response):
        super().test_recaltulate_permissions_superadmin(mock_celery_task_response)

    @pytest.mark.django_db
    def test_clear(self, is_preview=False):
        super().test_clear(is_preview=is_preview)

    @pytest.mark.django_db
    def test_clear_403(self, is_preview=False):
        super().test_clear_403(is_preview=is_preview)
