import json

import pytest
from django.core.cache import caches
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests.factories import (
    CharacterFactory,
    CharacterVariantFactory,
    DictionaryEntryFactory,
    get_site_with_member,
)
from backend.tests.test_apis.base_api_test import BaseSiteContentApiTest
from backend.tests.utils import equate_list_content_without_order
from backend.views.games_views import CACHE_KEY_WORDSY


class TestWordsyEndpoint(BaseSiteContentApiTest):
    """
    Tests for wordsy endpoint
    """

    API_LIST_VIEW = "api:wordsy-list"

    EXPECTED_ORTHOGRAPHY = ["a", "b", "c"]

    def setup_method(self):
        self.client = APIClient()
        self.site, self.member_user = get_site_with_member(
            Visibility.PUBLIC, Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=self.member_user)
        char_a = CharacterFactory.create(site=self.site, title="a", sort_order=1)
        char_b = CharacterFactory.create(site=self.site, title="b", sort_order=2)
        char_c = CharacterFactory.create(site=self.site, title="c", sort_order=3)
        CharacterVariantFactory.create(title="A", base_character=char_a)
        CharacterVariantFactory.create(title="B", base_character=char_b)
        CharacterVariantFactory.create(title="C", base_character=char_c)

    @pytest.mark.django_db
    def test_list_empty(self):
        # Overriding since there is no pagination class for this view
        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["orthography"] == self.EXPECTED_ORTHOGRAPHY
        assert response_data["words"] == []
        assert response_data["validGuesses"] == []
        assert response_data["solution"] == ""

    @pytest.mark.django_db
    def test_all_invalid_words(self):
        invalid_words_list = ["abc ab", "abcabc", "xyzav", "ab ab"]
        # adding multiple dictionary entries with bad title
        for title in invalid_words_list:
            DictionaryEntryFactory(
                site=self.site, visibility=Visibility.PUBLIC, title=title
            )
        # adding entries with good title but wrong properties
        DictionaryEntryFactory(
            site=self.site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.PHRASE,
            title="aaaaa",
        )
        DictionaryEntryFactory(
            site=self.site,
            visibility=Visibility.PUBLIC,
            exclude_from_kids=True,
            title="bbbbb",
        )
        DictionaryEntryFactory(
            site=self.site,
            visibility=Visibility.PUBLIC,
            exclude_from_games=True,
            title="ccccc",
        )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        assert response_data["orthography"] == self.EXPECTED_ORTHOGRAPHY
        assert response_data["words"] == []
        assert response_data["validGuesses"] == []
        assert response_data["solution"] == ""

    @pytest.mark.django_db
    def test_valid_words_plus_other_guesses(self):
        valid_words_list = ["abcab"]
        # adding some valid dictionary entries
        for title in valid_words_list:
            DictionaryEntryFactory(
                site=self.site, visibility=Visibility.PUBLIC, title=title
            )
        # adding entries with good title but wrong properties
        DictionaryEntryFactory(
            site=self.site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.PHRASE,
            title="aaaaa",
        )
        DictionaryEntryFactory(
            site=self.site,
            visibility=Visibility.PUBLIC,
            exclude_from_kids=True,
            title="Bbbbb",
        )
        DictionaryEntryFactory(
            site=self.site,
            visibility=Visibility.PUBLIC,
            exclude_from_games=True,
            title="CCCCC",
        )

        expected_words = valid_words_list
        expected_guesses = ["aaaaa", "bbbbb", "ccccc"] + valid_words_list

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        actual_words = response_data["words"]
        actual_valid_guesses = response_data["validGuesses"]

        assert equate_list_content_without_order(actual_words, expected_words)
        assert equate_list_content_without_order(actual_valid_guesses, expected_guesses)
        assert response_data["solution"] in expected_words

    @pytest.mark.django_db
    def test_mixed_words(self):
        CharacterFactory.create(site=self.site, title="aa", sort_order=4)

        # test to verify only valid words show up
        invalid_words_list = ["ab Ab", "abC ab", "abCabc", "Xyzav"]
        possible_guesses_list = ["aaaaa", "baaba"]
        valid_words_list = ["ABabA", "BcbCa", "aBcAb", "caBcA", "aaaaaaaaaa"]
        # base character form
        expected_words = ["ababa", "abcab", "bcbca", "cabca", "aaaaaaaaaa"]
        expected_guesses = expected_words + possible_guesses_list

        # adding multiple dictionary entries
        for title in invalid_words_list + valid_words_list + possible_guesses_list:
            DictionaryEntryFactory(
                site=self.site, visibility=Visibility.PUBLIC, title=title
            )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)

        actual_words = response_data["words"]
        actual_valid_guesses = response_data["validGuesses"]

        assert equate_list_content_without_order(actual_words, expected_words)
        assert equate_list_content_without_order(actual_valid_guesses, expected_guesses)
        assert response_data["solution"] in expected_words

    @pytest.mark.django_db
    def test_no_duplicate_words(self):
        DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="aaaaa"
        )
        DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="AaAaA"
        )
        DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="Bbbbb"
        )
        DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="BbBbB"
        )

        # no duplicates should be present
        expected_words = ["aaaaa", "bbbbb"]

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        response_data = json.loads(response.content)
        actual_words = response_data["words"]
        actual_valid_guesses = response_data["validGuesses"]

        assert equate_list_content_without_order(actual_words, expected_words)
        assert equate_list_content_without_order(actual_valid_guesses, expected_words)

    @pytest.mark.django_db
    def test_cache_used_word_deleted(self):
        # Verifying that data is being picked up from cache and not from db.
        dictionary_entry_1 = DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="aaaaa"
        )
        dictionary_entry_2 = DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="bbbbb"
        )
        valid_words_list = [dictionary_entry_1.title, dictionary_entry_2.title]

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        response_data = json.loads(response.content)
        assert response_data["words"] == valid_words_list
        assert response_data["validGuesses"] == valid_words_list

        # Deleting one entry
        dictionary_entry_2.delete()

        # Checking response again, the entry should still be present
        response_new = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        response_data_new = json.loads(response_new.content)
        assert "bbbbb" in response_data_new["words"]
        assert "bbbbb" in response_data_new["validGuesses"]

    @pytest.mark.django_db
    def test_cache_expiry_generates_new_config(self):
        # Then, Manually clearing cache to emulate end-of-day and
        # verifying that a new config is generated

        valid_words_list = ["aaaaa", "bbbbb"]
        for title in valid_words_list:
            DictionaryEntryFactory(
                site=self.site, visibility=Visibility.PUBLIC, title=title
            )

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        response_data = json.loads(response.content)
        assert response_data["words"] == valid_words_list
        assert response_data["validGuesses"] == valid_words_list
        assert response_data["solution"] in valid_words_list

        new_entry = DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="ccccc"
        )

        # Manually clearing the cache
        caches[CACHE_KEY_WORDSY].clear()

        # Fetching response again, the new entry should be now present in the words list
        # since cache is cleared, so the db should be accessed again
        response_new = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        response_data_new = json.loads(response_new.content)
        assert new_entry.title in response_data_new["words"]
        assert new_entry.title in response_data_new["validGuesses"]

    @pytest.mark.django_db
    def test_cache_expiry_visibility_changed(self):
        # Verifying that data is being picked up from cache and not from db.
        dictionary_entry_1 = DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="aaaaa"
        )
        dictionary_entry_2 = DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="bbbbb"
        )
        valid_words_list = [dictionary_entry_1.title, dictionary_entry_2.title]

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        response_data = json.loads(response.content)
        assert response_data["words"] == valid_words_list
        assert response_data["validGuesses"] == valid_words_list

        # Updating visibility of one entry
        dictionary_entry_2.visibility = Visibility.TEAM
        dictionary_entry_2.save()

        # Manually clearing the cache
        caches[CACHE_KEY_WORDSY].clear()

        # Checking response again, the updated entry should not show up
        response_new = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        response_data_new = json.loads(response_new.content)
        assert "bbbbb" not in response_data_new["words"]
        assert "bbbbb" not in response_data_new["validGuesses"]

    @pytest.mark.django_db
    def test_cache_expiry_word_deleted(self):
        # Verifying that data is being picked up from cache and not from db.
        DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="AAAAA"
        )
        dictionary_entry_2 = DictionaryEntryFactory(
            site=self.site, visibility=Visibility.PUBLIC, title="BBBBB"
        )
        valid_words_list = ["aaaaa", "bbbbb"]

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        response_data = json.loads(response.content)
        assert response_data["words"] == valid_words_list
        assert response_data["validGuesses"] == valid_words_list

        # Updating visibility of one entry
        dictionary_entry_2.delete()

        # Manually clearing the cache
        caches[CACHE_KEY_WORDSY].clear()

        # Checking response again, the deleted entry should not show up
        response_new = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))
        response_data_new = json.loads(response_new.content)
        assert "bbbbb" not in response_data_new["words"]
        assert "bbbbb" not in response_data_new["validGuesses"]
