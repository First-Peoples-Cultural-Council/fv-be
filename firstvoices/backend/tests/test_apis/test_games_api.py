import json

import pytest
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.tests.factories import (
    CharacterFactory,
    DictionaryEntryFactory,
    get_site_with_member,
)
from backend.tests.test_apis.base_api_test import BaseSiteContentApiTest


class TestWordsyEndpoint(BaseSiteContentApiTest):
    """
    Tests for wordsy endpoint
    """

    API_LIST_VIEW = "api:wordsy-list"

    def setup_method(self):
        self.client = APIClient()
        self.site, self.member_user = get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=self.member_user)
        CharacterFactory.create(site=self.site, title="a")
        CharacterFactory.create(site=self.site, title="b")
        CharacterFactory.create(site=self.site, title="c")

    @pytest.mark.django_db
    def test_list_empty(self):
        # Overriding since there is no pagination class for this view
        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["orthography"] == ["a", "b", "c"]
        assert response_data["words"] == []
        assert response_data["validGuesses"] == []
        assert response_data["solution"] == ""

    @pytest.mark.django_db
    def test_all_invalid_words(self):
        invalid_words_list = ["abc ab", "abcabc", "xyzav", "ab ab"]
        # adding multiple dictionary entries
        for title in invalid_words_list:
            DictionaryEntryFactory(
                site=self.site, visibility=Visibility.PUBLIC, title=title
            )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["orthography"] == ["a", "b", "c"]
        assert response_data["words"] == []
        assert response_data["validGuesses"] == []
        assert response_data["solution"] == ""

    @pytest.mark.django_db
    def test_mixed_words(self):
        # test to verify only valid words show up
        invalid_words_list = ["ab ab", "abc ab", "abcabc", "xyzav"]
        valid_words_list = ["ababa", "abcab", "bcbca", "cabca"]

        # adding multiple dictionary entries
        for title in invalid_words_list + valid_words_list:
            DictionaryEntryFactory(
                site=self.site, visibility=Visibility.PUBLIC, title=title
            )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["orthography"] == ["a", "b", "c"]
        assert response_data["words"] == valid_words_list
        assert response_data["validGuesses"] == valid_words_list
        assert response_data["solution"] in valid_words_list
