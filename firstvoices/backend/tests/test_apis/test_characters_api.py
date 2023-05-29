import json

import pytest

from backend.models.constants import Visibility
from backend.tests import factories

from .base_api_test import BaseReadOnlyUncontrolledSiteContentApiTest
from .base_media_test import RelatedMediaTestMixin


class TestCharactersEndpoints(
    RelatedMediaTestMixin, BaseReadOnlyUncontrolledSiteContentApiTest
):
    """
    End-to-end tests that the characters endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:character-list"
    API_DETAIL_VIEW = "api:character-detail"
    CHARACTER_NOTE = "Test note"

    def create_minimal_instance(self, site, visibility):
        return factories.CharacterFactory.create(
            site=site, note="a note", approximate_form="approx"
        )

    def create_instance_with_media(
        self,
        site,
        visibility,
        related_images=None,
        related_audio=None,
        related_videos=None,
    ):
        return factories.CharacterFactory.create(
            site=site,
            related_images=related_images,
            related_audio=related_audio,
            related_videos=related_videos,
        )

    def get_expected_response(self, instance, site):
        return {
            "url": f"http://testserver{self.get_detail_endpoint(key=instance.id, site_slug=site.slug)}",
            "id": str(instance.id),
            "title": instance.title,
            "sortOrder": instance.sort_order,
            "approximateForm": instance.approximate_form,
            "note": instance.note,
            "variants": [],
            "relatedEntries": [],
            "relatedAudio": [],
            "relatedImages": [],
            "relatedVideos": [],
        }

    @pytest.mark.django_db
    def test_detail_variants(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        character0 = factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            note=self.CHARACTER_NOTE,
        )

        character1 = factories.CharacterFactory.create(
            title="Ch1", site=site, sort_order=2, approximate_form="Ch1", note=""
        )

        variant = factories.CharacterVariantFactory.create(
            title="Ch0v0", base_character=character0
        )
        factories.CharacterVariantFactory.create(
            title="Ch0v1", base_character=character1
        )

        response = self.client.get(
            self.get_detail_endpoint(key=character0.id, site_slug=site.slug)
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["id"] == str(character0.id)
        assert len(response_data["variants"]) == 1
        assert response_data["variants"] == [
            {
                "title": variant.title,
            }
        ]

    @pytest.mark.django_db
    def test_detail_related_entries(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        character = factories.CharacterFactory.create(
            title="Ch0",
            site=site,
            sort_order=1,
            approximate_form="Ch0",
            note=self.CHARACTER_NOTE,
        )

        entry1 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryFactory.create(site=site)
        factories.DictionaryEntryRelatedCharacterFactory.create(
            character=character, dictionary_entry=entry1
        )
        factories.DictionaryEntryRelatedCharacterFactory.create(
            character=character, dictionary_entry=entry2
        )

        response = self.client.get(
            self.get_detail_endpoint(key=character.id, site_slug=site.slug)
        )

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["id"] == str(character.id)
        assert len(response_data["relatedEntries"]) == 1
        assert response_data["relatedEntries"] == [
            {
                "id": str(entry1.id),
                "title": entry1.title,
                "url": f"http://testserver/api/1.0/sites/{site.slug}/dictionary/{str(entry1.id)}/",
            }
        ]
