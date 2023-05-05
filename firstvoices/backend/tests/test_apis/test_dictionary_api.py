import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories

from ..factories import (
    AcknowledgementFactory,
    AlternateSpellingFactory,
    CategoryFactory,
    DictionaryEntryCategoryFactory,
    NoteFactory,
    PronunciationFactory,
    TranslationFactory,
)
from .base_api_test import BaseSiteControlledContentApiTest


class TestDictionaryEndpoint(BaseSiteControlledContentApiTest):
    """
    End-to-end tests that the dictionary endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:dictionaryentry-list"
    API_DETAIL_VIEW = "api:dictionaryentry-detail"

    def get_expected_response(self, entry, site):
        return {
            "url": f"http://testserver{self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))}",
            "id": str(entry.id),
            "title": entry.title,
            "type": "WORD",
            "customOrder": entry.custom_order,
            "visibility": "Public",
            "categories": [],
            "excludeFromGames": False,
            "excludeFromKids": False,
            "acknowledgements": [],
            "alternateSpellings": [],
            "notes": [],
            "translations": [],
            "pronunciations": [],
            "site": {
                "id": str(site.id),
                "title": site.title,
                "slug": site.slug,
                "url": f"http://testserver/api/1.0/sites/{site.slug}/",
                "language": None,
                "visibility": "Public",
            },
            "created": entry.created.astimezone().isoformat(),
            "lastModified": entry.last_modified.astimezone().isoformat(),
            "relatedEntries": [],
        }

    @pytest.mark.django_db
    def test_list_full(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.MEMBERS
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][0] == self.get_expected_response(entry, site)

    @pytest.mark.django_db
    def test_list_permissions(self):
        # create some visible words and some invisible words
        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)
        factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.MEMBERS
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["count"] == 1, "did not filter out blocked sites"
        assert len(response_data["results"]) == 1, "did not include available site"

    @pytest.mark.django_db
    def test_detail(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == self.get_expected_response(entry, site)

    @pytest.mark.parametrize(
        "field",
        [
            {"factory": AlternateSpellingFactory, "name": "alternateSpellings"},
            {"factory": AcknowledgementFactory, "name": "acknowledgements"},
            {"factory": NoteFactory, "name": "notes"},
            {"factory": PronunciationFactory, "name": "pronunciations"},
        ],
        ids=["alternateSpellings", "acknowledgements", "notes", "pronunciations"],
    )
    @pytest.mark.django_db
    def test_detail_fields(self, field):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)

        text = "bon mots"
        model = field["factory"].create(dictionary_entry=entry, text=text)

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data[field["name"]] == [
            {"id": str(model.id), "text": f"{text}"}
        ]

    @pytest.mark.django_db
    def test_detail_translations(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)

        text = "bon mots"
        model = TranslationFactory.create(dictionary_entry=entry, text=text)

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["translations"] == [
            {
                "id": str(model.id),
                "text": f"{text}",
                "language": "EN",
                "partOfSpeech": None,
            }
        ]

    @pytest.mark.django_db
    def test_detail_categories(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )

        category1 = CategoryFactory(site=site, title="test category A")
        CategoryFactory(site=site, title="test category B")
        CategoryFactory(site=site)

        DictionaryEntryCategoryFactory(category=category1, dictionary_entry=entry)

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["categories"] == [
            {
                "title": f"{category1.title}",
                "id": str(category1.id),
                "url": f"http://testserver/api/1.0/sites/{site.slug}/categories/{str(category1.id)}/",
            },
        ]

    @pytest.mark.django_db
    def test_detail_related_entries(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(visibility=Visibility.PUBLIC)
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry2 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC
        )
        entry3 = factories.DictionaryEntryFactory.create(
            site=site, visibility=Visibility.TEAM
        )
        factories.DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)

        factories.DictionaryEntryLinkFactory(
            from_dictionary_entry=entry, to_dictionary_entry=entry2
        )
        factories.DictionaryEntryLinkFactory(
            from_dictionary_entry=entry, to_dictionary_entry=entry3
        )

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert (
            len(response_data["relatedEntries"]) >= 1
        ), "Did not include related entry"
        assert (
            not len(response_data["relatedEntries"]) > 1
        ), "Did not block private related entry"
        assert response_data["relatedEntries"] == [
            {
                "id": str(entry2.id),
                "title": entry2.title,
                "url": f"http://testserver/api/1.0/sites/{site.slug}/dictionary/{str(entry2.id)}/",
            }
        ]

    @pytest.mark.django_db
    def test_detail_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(
            visibility=Visibility.TEAM, site=site
        )

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["id"] == str(entry.id)

    @pytest.mark.django_db
    def test_detail_403_entry_not_visible(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(
            visibility=Visibility.TEAM, site=site
        )

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_detail_404_unknown_site(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        entry = factories.DictionaryEntryFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.get(
            self.get_detail_endpoint(site_slug="fake-site", key=str(entry.id))
        )

        assert response.status_code == 404
