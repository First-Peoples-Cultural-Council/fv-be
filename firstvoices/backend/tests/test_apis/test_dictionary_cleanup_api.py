import json
from unittest.mock import ANY

import pytest
from django.urls import reverse

from backend.models import DictionaryEntry
from backend.models.constants import AppRole, Visibility
from backend.tests import factories
from backend.tests.test_apis.base_api_test import BaseApiTest


class TestDictionaryCleanupPreview(BaseApiTest):
    API_DETAIL_VIEW = "api:dictionary-cleanup-preview-list"
    SUCCESS_MESSAGE = {"message": "Recalculation preview has been queued."}

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

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    def test_recalculate_post(
        self,
        celery_session_worker,
        celery_session_app,
        django_db_serialized_rollback,
    ):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        factories.DictionaryEntryFactory.create(site=site, title="test")

        response = self.client.post(self.get_detail_endpoint(site.slug))

        response_data = json.loads(response.content)
        assert response.status_code == 202
        assert response_data == self.SUCCESS_MESSAGE

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    def test_recalculate_e2e(
        self,
        celery_session_worker,
        celery_session_app,
        django_db_serialized_rollback,
    ):
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

        response_post = self.client.post(self.get_detail_endpoint(site.slug))

        response_post_data = json.loads(response_post.content)
        assert response_post.status_code == 202
        assert response_post_data == self.SUCCESS_MESSAGE

        response_get = self.client.get(self.get_detail_endpoint(site.slug))

        response_get_data = json.loads(response_get.content)
        assert response_get.status_code == 200
        assert response_get_data["results"] == self.get_expected_response(site=site)

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    def test_recalculate_permissions(
        self,
        celery_session_worker,
        celery_session_app,
        django_db_serialized_rollback,
    ):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        factories.DictionaryEntryFactory.create(site=site, title="test")

        response_post = self.client.post(self.get_detail_endpoint(site.slug))
        response_post_data = json.loads(response_post.content)

        assert response_post.status_code == 202
        assert response_post_data == self.SUCCESS_MESSAGE

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response_get = self.client.get(self.get_detail_endpoint(site.slug))
        response_get_data = json.loads(response_get.content)

        assert response_get.status_code == 200
        assert response_get_data["results"] == []


class TestDictionaryCleanup(TestDictionaryCleanupPreview):
    API_DETAIL_VIEW = "api:dictionary-cleanup-list"
    SUCCESS_MESSAGE = {"message": "Recalculation has been queued."}

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

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    def test_recalculate_e2e(
        self,
        celery_session_worker,
        celery_session_app,
        django_db_serialized_rollback,
    ):
        super().test_recalculate_e2e(
            celery_session_worker, celery_session_app, django_db_serialized_rollback
        )
        entry = DictionaryEntry.objects.get(title="test")
        entry2 = DictionaryEntry.objects.get(title="AAA")
        assert DictionaryEntry.objects.get(id=entry.id).title == "test"
        assert DictionaryEntry.objects.get(id=entry.id).custom_order == "!#$!"
        assert DictionaryEntry.objects.get(id=entry2.id).title == "AAA"
        assert DictionaryEntry.objects.get(id=entry2.id).custom_order == "%%%"
