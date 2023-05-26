import json
from unittest.mock import ANY

import pytest
from django.urls import reverse

from backend.models.constants import AppRole, Visibility
from backend.tests import factories
from backend.tests.test_apis.base_api_test import BaseApiTest


class TestDictionaryCleanupPreview(BaseApiTest):
    API_DETAIL_VIEW = "api:site-detail"
    SUPERADMIN_PERMISSION = "views.has_custom_order_access"

    def get_detail_endpoint(self, key):
        return (
            reverse(self.API_DETAIL_VIEW, current_app=self.APP_NAME, args=[key])
            + "dictionary-cleanup/preview/"
        )

    @pytest.mark.django_db
    def test_recalculate_preview_get_404(self):
        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_detail_endpoint("missing-slug"))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_recalculate_preview_post_404(self):
        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_detail_endpoint("missing-slug"))
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_recalculate_preview_post_403(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)
        user = factories.get_anonymous_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.get_detail_endpoint(site.slug))
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_recalculate_preview_get_empty(self):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        assert user.has_perm(self.SUPERADMIN_PERMISSION, site)

        response = self.client.get(self.get_detail_endpoint(site.slug))
        response_data = json.loads(response.content)
        assert response.status_code == 200
        assert response_data["results"] == []

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    def test_recalculate_preview_post(
        self, celery_worker, django_db_serialized_rollback
    ):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        assert user.has_perm(self.SUPERADMIN_PERMISSION, site)

        factories.DictionaryEntryFactory.create(site=site, title="test")

        response = self.client.post(self.get_detail_endpoint(site.slug))

        response_data = json.loads(response.content)
        assert response.status_code == 201
        assert response_data == {"message": "Recalculation preview has been queued."}

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    def test_recalculate_preview_full(
        self, celery_worker, django_db_serialized_rollback
    ):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)
        assert user.has_perm(self.SUPERADMIN_PERMISSION, site)

        factories.DictionaryEntryFactory.create(site=site, title="test")

        response_post = self.client.post(self.get_detail_endpoint(site.slug))
        response_post_data = json.loads(response_post.content)

        assert response_post.status_code == 201
        assert response_post_data == {
            "message": "Recalculation preview has been queued."
        }

        response_get = self.client.get(self.get_detail_endpoint(site.slug))
        response_get_data = json.loads(response_get.content)

        assert response_get.status_code == 200
        assert response_get_data["results"] == [
            {
                "site": site.title,
                "currentPreviewTaskStatus": "SUCCESS",
                "latestRecalculationDate": ANY,
                "latestRecalculationResult": {
                    "updatedEntries": [],
                    "unknownCharacterCount": {"⚑e": 1, "⚑s": 1, "⚑t": 2},
                },
            }
        ]

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    def test_recalculate_preview_get_permissions(
        self, celery_worker, django_db_serialized_rollback
    ):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        factories.DictionaryEntryFactory.create(site=site, title="test")

        self.client.post(self.get_detail_endpoint(site.slug))

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response_get = self.client.get(self.get_detail_endpoint(site.slug))
        response_get_data = json.loads(response_get.content)

        assert response_get.status_code == 200
        assert response_get_data["results"] == []
