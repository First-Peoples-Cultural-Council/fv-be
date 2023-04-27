import json

import pytest

from factory.django import DjangoModelFactory

from backend.models import dictionary
from backend.models.constants import Role, Visibility
from backend.tests import factories

from .base_api_test import BaseSiteContentApiTest


class AcknowledgementFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.DictionaryAcknowledgement


class AlternateSpellingFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.AlternateSpelling


class NoteFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.DictionaryNote


class PronunciationFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.Pronunciation


class TranslationFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.DictionaryTranslation


class TestDictionaryEndpoint(BaseSiteContentApiTest):
    """
    End-to-end tests that the dictionary endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:dictionary-list"
    API_DETAIL_VIEW = "api:dictionary-detail"

    @pytest.mark.django_db
    def test_list_404_site_not_found(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site_slug="missing-site"))

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_list_403_site_not_visible(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_list_empty(self):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 0
        assert response_data["count"] == 0

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

        assert response_data["results"][0] == {
            "url": f"http://testserver{self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))}",
            "id": str(entry.id),
            "title": entry.title,
            "type": "WORD",
            "customOrder": entry.custom_order,
            "visibility": "Public",
            "category": None,
            "excludeFromGames": False,
            "excludeFromKids": False,
            "acknowledgements": [],
            "alternateSpellings": [],
            "notes": [],
            "translations": [],
            "pronunciations": [],
            "site": site.title,
            "created": entry.created.astimezone().isoformat(),
            "lastModified": entry.last_modified.astimezone().isoformat(),
        }

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
        assert response_data == {
            "url": f"http://testserver{self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))}",
            "id": str(entry.id),
            "title": entry.title,
            "type": "WORD",
            "customOrder": entry.custom_order,
            "visibility": "Public",
            "category": None,
            "excludeFromGames": False,
            "excludeFromKids": False,
            "acknowledgements": [],
            "alternateSpellings": [],
            "notes": [],
            "translations": [],
            "pronunciations": [],
            "site": site.title,
            "created": entry.created.astimezone().isoformat(),
            "lastModified": entry.last_modified.astimezone().isoformat(),
        }

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
        field["factory"].create(dictionary_entry=entry, text=text)

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data[field["name"]] == [{"text": f"{text}"}]

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
        TranslationFactory.create(dictionary_entry=entry, text=text)

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key=str(entry.id))
        )

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["translations"] == [
            {
                "text": f"{text}",
                "language": "EN",
                "partOfSpeech": None,
            }
        ]

    @pytest.mark.django_db
    def test_list_team_access(self):
        site = factories.SiteFactory.create(visibility=Visibility.TEAM)
        user = factories.get_non_member_user()
        factories.MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"] == []

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

    @pytest.mark.django_db
    def test_detail_404_unknown_entry(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_detail_endpoint(site_slug=site.slug, key="fake-word")
        )

        assert response.status_code == 404
