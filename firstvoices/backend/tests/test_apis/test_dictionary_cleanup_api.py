import json
from unittest.mock import ANY

import pytest

from backend.models import DictionaryEntry
from backend.models.constants import AppRole, Visibility
from backend.tests import factories
from backend.tests.test_apis.base_api_test import BaseApiTest

RECALCULATION_CONFIRMATION_MESSAGE = {"message": "Recalculation has been queued."}
RECALCULATION_PREVIEW_CONFIRMATION_MESSAGE = {
    "message": "Recalculation preview has been queued."
}


class TestDictionaryCleanup(BaseApiTest):
    API_DETAIL_VIEW = "api:site-detail"

    def get_cleanup_endpoint(self, key, is_preview):
        if is_preview:
            return self.get_detail_endpoint(key) + "dictionary-cleanup/preview/"
        else:
            return self.get_detail_endpoint(key) + "dictionary-cleanup/"

    @pytest.mark.django_db
    @pytest.mark.parametrize("is_preview", [True, False])
    def test_recalculate_get_404(self, is_preview):
        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_cleanup_endpoint("missing-slug", is_preview=is_preview)
        )
        assert response.status_code == 404

    @pytest.mark.django_db
    @pytest.mark.parametrize("is_preview", [True, False])
    def test_recalculate_post_404(self, is_preview):
        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.post(
            self.get_cleanup_endpoint("missing-slug", is_preview=is_preview)
        )
        assert response.status_code == 404

    @pytest.mark.django_db
    @pytest.mark.parametrize("is_preview", [True, False])
    def test_recalculate_post_403(self, is_preview):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.post(
            self.get_cleanup_endpoint(site.slug, is_preview=is_preview)
        )
        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize("is_preview", [True, False])
    def test_recalculate_get_empty(self, is_preview):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_cleanup_endpoint(site.slug, is_preview=True)
        )
        response_data = json.loads(response.content)
        assert response.status_code == 200
        assert response_data["results"] == []

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    @pytest.mark.parametrize(
        "is_preview, result",
        [
            (True, RECALCULATION_PREVIEW_CONFIRMATION_MESSAGE),
            (False, RECALCULATION_CONFIRMATION_MESSAGE),
        ],
    )
    def test_recalculate_post(
        self,
        celery_session_worker,
        celery_session_app,
        django_db_serialized_rollback,
        is_preview,
        result,
    ):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        factories.DictionaryEntryFactory.create(site=site, title="test")

        response = self.client.post(
            self.get_cleanup_endpoint(site.slug, is_preview=is_preview)
        )

        response_data = json.loads(response.content)
        assert response.status_code == 201
        assert response_data == result

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    @pytest.mark.parametrize(
        "is_preview, message",
        [
            (True, RECALCULATION_PREVIEW_CONFIRMATION_MESSAGE),
            (False, RECALCULATION_CONFIRMATION_MESSAGE),
        ],
    )
    def test_recalculate_e2e(
        self,
        celery_session_worker,
        celery_session_app,
        django_db_serialized_rollback,
        is_preview,
        message,
    ):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        alphabet = factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site, title="tèst")
        factories.CharacterFactory.create(site=site, title="t")
        factories.CharacterFactory.create(site=site, title="e")
        factories.CharacterFactory.create(site=site, title="s")
        alphabet.input_to_canonical_map = [{"in": "è", "out": "e"}]
        alphabet.save()

        response_post = self.client.post(
            self.get_cleanup_endpoint(site.slug, is_preview=is_preview)
        )

        response_post_data = json.loads(response_post.content)
        assert response_post.status_code == 201
        assert response_post_data == message

        response_get = self.client.get(
            self.get_cleanup_endpoint(site.slug, is_preview=is_preview)
        )

        response_get_data = json.loads(response_get.content)
        assert response_get.status_code == 200
        assert response_get_data["results"] == [
            {
                "site": site.title,
                "currentTaskStatus": "SUCCESS",
                "latestRecalculationDate": ANY,
                "latestRecalculationResult": {
                    "unknownCharacterCount": {},
                    "updatedEntries": [
                        {
                            "title": "tèst",
                            "cleanedTitle": "test",
                            "isTitleUpdated": True,
                            "previousCustomOrder": "⚑t⚑è⚑s⚑t",
                            "newCustomOrder": "!#$!",
                        },
                    ],
                },
            }
        ]

        if not is_preview:
            assert DictionaryEntry.objects.get(id=entry.id).title == "test"
            assert DictionaryEntry.objects.get(id=entry.id).custom_order == "!#$!"

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    @pytest.mark.parametrize(
        "is_preview, message",
        [
            (True, RECALCULATION_PREVIEW_CONFIRMATION_MESSAGE),
            (False, RECALCULATION_CONFIRMATION_MESSAGE),
        ],
    )
    def test_recalculate_e2e_multiple_entries(
        self,
        celery_session_worker,
        celery_session_app,
        django_db_serialized_rollback,
        is_preview,
        message,
    ):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        alphabet = factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(site=site, title="tèst")
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

        response_post = self.client.post(
            self.get_cleanup_endpoint(site.slug, is_preview=is_preview)
        )

        response_post_data = json.loads(response_post.content)
        assert response_post.status_code == 201
        assert response_post_data == message

        response_get = self.client.get(
            self.get_cleanup_endpoint(site.slug, is_preview=is_preview)
        )

        response_get_data = json.loads(response_get.content)
        assert response_get.status_code == 200
        assert response_get_data["results"] == [
            {
                "site": site.title,
                "currentTaskStatus": "SUCCESS",
                "latestRecalculationDate": ANY,
                "latestRecalculationResult": {
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

        if not is_preview:
            assert DictionaryEntry.objects.get(id=entry.id).title == "test"
            assert DictionaryEntry.objects.get(id=entry.id).custom_order == "!#$!"
            assert DictionaryEntry.objects.get(id=entry2.id).title == "AAA"
            assert DictionaryEntry.objects.get(id=entry2.id).custom_order == "%%%"

    @pytest.mark.django_db(transaction=True, serialized_rollback=True)
    @pytest.mark.parametrize(
        "is_preview, message",
        [
            (True, RECALCULATION_PREVIEW_CONFIRMATION_MESSAGE),
            (False, RECALCULATION_CONFIRMATION_MESSAGE),
        ],
    )
    def test_recalculate_permissions(
        self,
        celery_session_worker,
        celery_session_app,
        django_db_serialized_rollback,
        is_preview,
        message,
    ):
        site = factories.SiteFactory.create(slug="test", visibility=Visibility.PUBLIC)
        factories.AlphabetFactory.create(site=site)

        user = factories.get_app_admin(role=AppRole.SUPERADMIN)
        self.client.force_authenticate(user=user)

        factories.DictionaryEntryFactory.create(site=site, title="test")

        response_post = self.client.post(
            self.get_cleanup_endpoint(site.slug, is_preview=is_preview)
        )
        response_post_data = json.loads(response_post.content)

        assert response_post.status_code == 201
        assert response_post_data == message

        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response_get = self.client.get(
            self.get_cleanup_endpoint(site.slug, is_preview=is_preview)
        )
        response_get_data = json.loads(response_get.content)

        assert response_get.status_code == 200
        assert response_get_data["results"] == []
