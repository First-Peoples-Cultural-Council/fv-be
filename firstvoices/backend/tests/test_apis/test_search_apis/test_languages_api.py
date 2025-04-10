import json

import pytest

import backend.tests.factories.access
from backend.models.constants import Visibility
from backend.tests import factories
from backend.tests.factories.access import (
    get_anonymous_user,
    get_non_member_user,
    get_superadmin,
)
from backend.tests.test_apis.base.base_api_test import BaseApiTest
from backend.tests.test_apis.base.base_media_test import MediaTestMixin
from backend.tests.test_apis.test_search_apis.base_search_test import SearchMocksMixin


class TestLanguagesEndpoints(MediaTestMixin, SearchMocksMixin, BaseApiTest):
    """
    End-to-end tests that the languages endpoints have the expected behaviour.

    See also test_search_querying package.
    """

    API_LIST_VIEW = "api:language-list"
    API_DETAIL_VIEW = "api:language-detail"

    def get_search_endpoint(self):
        return f"{self.get_list_endpoint()}?q=what"

    def get_list_response(self, mock_search_query_execute, language_search_results):
        return self.get_response(
            self.get_list_endpoint(), mock_search_query_execute, language_search_results
        )

    def get_search_response(self, mock_search_query_execute, language_search_results):
        return self.get_response(
            self.get_search_endpoint(),
            mock_search_query_execute,
            language_search_results,
        )

    def get_response(self, url, mock_search_query_execute, language_search_results):
        mock_hits = [
            self.format_language_hit(language) for language in language_search_results
        ]

        mock_results = {
            "hits": {
                "hits": mock_hits,
                "total": {"value": len(mock_hits), "relation": "eq"},
            }
        }
        mock_search_query_execute.return_value = mock_results
        return self.client.get(url)

    def format_language_hit(self, language):
        return {
            "_index": "language_2024_01_25_00_03_01",
            "_type": "_doc",
            "_id": str(
                language.id
            ),  # using this as a unique id to mimic the id of an index document
            "_score": None,
            "_source": {
                "document_id": str(language.id),
                "document_type": "Language",
            },
        }

    @pytest.mark.parametrize(
        "get_response", ["get_list_response", "get_search_response"]
    )
    @pytest.mark.django_db
    def test_empty_results(
        self, get_response, db, mock_search_query_execute, mock_get_page_size
    ):
        response = getattr(self, get_response)(mock_search_query_execute, [])

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["count"] == 0
        assert response_data["results"] == []

    @pytest.mark.parametrize(
        "get_response", ["get_list_response", "get_search_response"]
    )
    @pytest.mark.django_db
    def test_one_language_is_formatted(
        self, get_response, db, mock_search_query_execute, mock_get_page_size
    ):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        language = backend.tests.factories.access.LanguageFactory.create(
            title="Language 0"
        )
        site = factories.SiteFactory(language=language, visibility=Visibility.PUBLIC)

        response = getattr(self, get_response)(mock_search_query_execute, [language])

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        language_response = response_data["results"][0]
        self.assert_language_response(language, language_response)

        assert len(language_response["sites"]) == 1
        self.assert_site_response(site, language_response["sites"][0])

    @pytest.mark.parametrize(
        "get_response", ["get_list_response", "get_search_response"]
    )
    @pytest.mark.parametrize(
        "get_user", [get_anonymous_user, get_non_member_user, get_superadmin]
    )
    @pytest.mark.django_db
    def test_language_sites_only_include_visible(
        self, get_response, get_user, db, mock_search_query_execute, mock_get_page_size
    ):
        user = get_user()
        self.client.force_authenticate(user=user)

        language = backend.tests.factories.access.LanguageFactory.create(
            title="waffles"
        )
        site_public = factories.SiteFactory(
            language=language, visibility=Visibility.PUBLIC
        )
        site_members = factories.SiteFactory(
            language=language, visibility=Visibility.MEMBERS
        )
        site_team = factories.SiteFactory(language=language, visibility=Visibility.TEAM)
        site_hidden = factories.SiteFactory(
            language=language, visibility=Visibility.PUBLIC, is_hidden=True
        )

        response = getattr(self, get_response)(mock_search_query_execute, [language])

        assert response.status_code == 200

        response_data = json.loads(response.content)
        site_id_list = [site["id"] for site in response_data["results"][0]["sites"]]
        assert len(site_id_list) == 2
        assert str(site_public.id) in site_id_list
        assert str(site_members.id) in site_id_list
        assert str(site_team.id) not in site_id_list
        assert str(site_hidden.id) not in site_id_list

    @pytest.mark.parametrize(
        "get_response", ["get_list_response", "get_search_response"]
    )
    @pytest.mark.django_db
    def test_language_sites_are_sorted(
        self, get_response, db, mock_search_query_execute, mock_get_page_size
    ):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        language = backend.tests.factories.access.LanguageFactory.create(
            title="waffles"
        )
        site_z = factories.SiteFactory(
            title="zebra", language=language, visibility=Visibility.PUBLIC
        )
        site_a = factories.SiteFactory(
            title="apple", language=language, visibility=Visibility.PUBLIC
        )

        response = getattr(self, get_response)(mock_search_query_execute, [language])

        assert response.status_code == 200

        response_data = json.loads(response.content)
        site_list = response_data["results"][0]["sites"]
        self.assert_site_response(site_a, site_list[0])
        self.assert_site_response(site_z, site_list[1])

    @pytest.mark.parametrize(
        "get_response", ["get_list_response", "get_search_response"]
    )
    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_logo(
        self, get_response, visibility, mock_search_query_execute, mock_get_page_size
    ):
        """
        Set this up specially to make sure logo is from same site (doesn't happen by default in the factories).
        """
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        language = factories.LanguageFactory.create()
        site = factories.SiteFactory.create(visibility=visibility, language=language)
        image = factories.ImageFactory(site=site)
        site.logo = image
        site.save()

        response = getattr(self, get_response)(mock_search_query_execute, [language])

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["results"][0]["sites"][0][
            "logo"
        ] == self.get_expected_image_data(image)

    @pytest.mark.django_db
    def test_list_more_sites_are_formatted(
        self, db, mock_search_query_execute, mock_get_page_size
    ):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site = factories.SiteFactory(language=None, visibility=Visibility.PUBLIC)

        response = self.get_list_response(mock_search_query_execute, [])

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert (
            len(response_data["results"]) == 1
        )  # checking results not count until fw-5519 fixes pagination

        language_response = response_data["results"][0]
        self.assert_language_placeholder_response(language_response)

        assert len(language_response["sites"]) == 1
        self.assert_site_response(site, language_response["sites"][0])

    @pytest.mark.django_db
    def test_list_more_sites_at_end(
        self, db, mock_search_query_execute, mock_get_page_size
    ):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        language = backend.tests.factories.access.LanguageFactory.create(
            title="Language 0"
        )
        site = factories.SiteFactory(language=language, visibility=Visibility.PUBLIC)

        site2 = factories.SiteFactory(language=None, visibility=Visibility.PUBLIC)

        response = self.get_list_response(mock_search_query_execute, [language])

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 2

        language_response = response_data["results"][0]
        self.assert_language_response(language, language_response)
        assert len(language_response["sites"]) == 1
        self.assert_site_response(site, language_response["sites"][0])

        more_sites_response = response_data["results"][1]
        self.assert_language_placeholder_response(more_sites_response)
        assert len(more_sites_response["sites"]) == 1
        self.assert_site_response(site2, more_sites_response["sites"][0])

    @pytest.mark.django_db
    def test_list_more_sites_are_sorted(
        self, db, mock_search_query_execute, mock_get_page_size
    ):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        site_z = factories.SiteFactory(
            title="Zoolander", language=None, visibility=Visibility.PUBLIC
        )
        site_m = factories.SiteFactory(
            title="Mac And Cheese", language=None, visibility=Visibility.PUBLIC
        )
        site_a = factories.SiteFactory(
            title="atreyu", language=None, visibility=Visibility.PUBLIC
        )

        response = self.get_list_response(mock_search_query_execute, [])

        assert response.status_code == 200

        response_data = json.loads(response.content)
        site_list = response_data["results"][0]["sites"]

        self.assert_site_response(site_a, site_list[0])
        self.assert_site_response(site_m, site_list[1])
        self.assert_site_response(site_z, site_list[2])

    @pytest.mark.parametrize(
        "get_user", [get_anonymous_user, get_non_member_user, get_superadmin]
    )
    @pytest.mark.django_db
    def test_list_more_sites_only_include_visible(
        self, get_user, db, mock_search_query_execute, mock_get_page_size
    ):
        user = get_user()
        self.client.force_authenticate(user=user)

        site_public = factories.SiteFactory(language=None, visibility=Visibility.PUBLIC)
        site_members = factories.SiteFactory(
            language=None, visibility=Visibility.MEMBERS
        )
        site_team = factories.SiteFactory(language=None, visibility=Visibility.TEAM)
        site_hidden = factories.SiteFactory(
            language=None, visibility=Visibility.PUBLIC, is_hidden=True
        )

        response = self.get_list_response(mock_search_query_execute, [])

        assert response.status_code == 200

        response_data = json.loads(response.content)
        site_id_list = [site["id"] for site in response_data["results"][0]["sites"]]
        assert len(site_id_list) == 2

        assert str(site_public.id) in site_id_list
        assert str(site_members.id) in site_id_list

        assert str(site_team.id) not in site_id_list
        assert str(site_hidden.id) not in site_id_list

    @pytest.mark.django_db
    def test_search_mixed_sites_and_languages(self, db, mock_search_query_execute):
        user = factories.get_non_member_user()
        self.client.force_authenticate(user=user)

        language = backend.tests.factories.access.LanguageFactory.create()
        language_site = factories.SiteFactory(
            language=language, visibility=Visibility.PUBLIC
        )

        single_site_1 = factories.SiteFactory(
            language=None, visibility=Visibility.PUBLIC
        )
        single_site_2 = factories.SiteFactory(
            language=None, visibility=Visibility.PUBLIC
        )

        mock_hits = [
            {
                "_index": "language_2024_01_25_00_03_01",
                "_type": "_doc",
                "_id": "abc123",
                "_score": None,
                "_source": {
                    "document_id": str(single_site_2.id),
                    "document_type": "Site",
                },
            },
            {
                "_index": "language_2024_01_25_00_03_01",
                "_type": "_doc",
                "_id": "xyz123",
                "_score": None,
                "_source": {
                    "document_id": str(language.id),
                    "document_type": "Language",
                },
            },
            {
                "_index": "language_2024_01_25_00_03_01",
                "_type": "_doc",
                "_id": "ghi789",
                "_score": None,
                "_source": {
                    "document_id": str(single_site_1.id),
                    "document_type": "Site",
                },
            },
        ]

        mock_results = {
            "hits": {
                "hits": mock_hits,
                "total": {"value": len(mock_hits), "relation": "eq"},
            }
        }
        mock_search_query_execute.return_value = mock_results
        response = self.client.get(self.get_search_endpoint())

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert len(response_data["results"]) == 3

        self.assert_language_placeholder_response(response_data["results"][0])
        self.assert_site_response(
            single_site_2, response_data["results"][0]["sites"][0]
        )

        self.assert_language_response(language, response_data["results"][1])
        self.assert_site_response(
            language_site, response_data["results"][1]["sites"][0]
        )

        self.assert_language_placeholder_response(response_data["results"][2])
        self.assert_site_response(
            single_site_1, response_data["results"][2]["sites"][0]
        )

    def assert_language_response(self, language, language_response):
        assert language_response["language"] == language.title
        assert language_response["languageCode"] == language.language_code
        assert language_response["id"] == str(language.id)

    def assert_language_placeholder_response(self, language_placeholder_response):
        assert language_placeholder_response["language"] == ""
        assert language_placeholder_response["languageCode"] == ""
        assert "-placeholder" in language_placeholder_response["id"]
        assert language_placeholder_response["noLanguageAssigned"]

    def assert_site_response(self, site, site_response):
        assert site_response == {
            "id": str(site.id),
            "title": site.title,
            "slug": site.slug,
            "language": site.language.title if site.language else None,
            "visibility": "public",
            "logo": None,
            "url": f"http://testserver/api/1.0/sites/{site.slug}",
            "enabledFeatures": [],
            "isHidden": False,
        }
