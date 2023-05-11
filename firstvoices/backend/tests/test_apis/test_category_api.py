import json

import pytest
from rest_framework.test import APIClient

from backend.models.constants import AppRole
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests.factories import DictionaryEntryFactory, SiteFactory, get_app_admin
from backend.tests.factories.base import ChildCategoryFactory, ParentCategoryFactory
from backend.tests.test_apis.base_api_test import BaseSiteContentApiTest


class TestCategoryEndpoints(BaseSiteContentApiTest):
    """
    End-to-end tests that the category endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:category-list"
    API_DETAIL_VIEW = "api:category-detail"

    def setup_method(self):
        self.client = APIClient()
        self.user = get_app_admin(AppRole.STAFF)
        self.client.force_authenticate(user=self.user)
        self.site = SiteFactory.create()

    def get_categories_with_word_phrase(self):
        word_entry = DictionaryEntryFactory(site=self.site)
        category_word = ParentCategoryFactory(site=self.site)
        category_word.dictionary_entries.add(word_entry)

        phrase_entry = DictionaryEntryFactory(
            site=self.site, type=TypeOfDictionaryEntry.PHRASE
        )
        category_phrase = ParentCategoryFactory(site=self.site)
        category_phrase.dictionary_entries.add(phrase_entry)

        return word_entry, phrase_entry, category_word, category_phrase

    @pytest.mark.django_db
    def test_list_empty(self):
        """
        Since categories are always generated when a site is initialized. Thus, there will generally not be a case
        where an empty category list exists. Overriding this test case from baseclass and marking it passed.
        """
        pass

    @pytest.mark.django_db
    def test_category_list_full(self):
        """Assuming a new site will have at least 1 category."""

        response = self.client.get(self.get_list_endpoint(self.site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] > 0

        category_json = response_data["results"][0]
        # Testing general structure of the response json.
        # Specific testing done in the retrieve view test
        assert "id" in category_json
        assert "title" in category_json
        assert "children" in category_json
        assert isinstance(category_json["children"], list)
        assert "description" in category_json

    @pytest.mark.django_db
    def test_detail_parent_category(self):
        parent_category = ParentCategoryFactory.create(site=self.site)
        child_category = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )
        detail_endpoint = self.get_detail_endpoint(self.site.slug, parent_category.id)
        response = self.client.get(detail_endpoint)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {
            "id": str(parent_category.id),
            "title": parent_category.title,
            "description": parent_category.description,
            "children": [
                {
                    "id": str(child_category.id),
                    "title": child_category.title,
                    "description": child_category.description,
                }
            ],
            "parent": None,
        }

    @pytest.mark.django_db
    def test_detail_children_category(self):
        parent_category = ParentCategoryFactory.create(site=self.site)
        child_category = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )

        detail_endpoint = self.get_detail_endpoint(self.site.slug, child_category.id)

        response = self.client.get(detail_endpoint)
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {
            "id": str(child_category.id),
            "title": child_category.title,
            "description": child_category.description,
            "children": [],
            "parent": str(parent_category.id),
        }

    @pytest.mark.django_db
    def test_detail_404(self):
        wrong_endpoint = self.get_detail_endpoint(self.site.slug, "54321")
        response = self.client.get(wrong_endpoint)
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "invalid_flags, expected_count",
        [
            ("invalid_value", 0),
            ("WORD|invalid_Value", 1),
            ("PHRASE|WORD|invalid_Value", 2),
        ],
    )
    @pytest.mark.django_db
    def test_invalid_flags_for_contains_param(self, invalid_flags, expected_count):
        """If invalid flag present in contains param, ignore the flag and return all entries."""
        word_entry = DictionaryEntryFactory(site=self.site)
        phrase_entry = DictionaryEntryFactory(
            site=self.site, type=TypeOfDictionaryEntry.PHRASE
        )

        category_word = ParentCategoryFactory(site=self.site)
        category_phrase = ParentCategoryFactory(site=self.site)

        category_word.dictionary_entries.add(word_entry)
        category_phrase.dictionary_entries.add(phrase_entry)

        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug, query_kwargs={"contains": invalid_flags}
            )
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == expected_count

    @pytest.mark.parametrize(
        "flag, expected_count", [("WORD", 1), ("word", 1), ("WorD", 1)]
    )
    @pytest.mark.django_db
    def test_contains_word(self, flag, expected_count):
        # One category is added for a word and one for a phrase
        # Test should return only that entry which has the word associated with it

        _, _, category_word, category_phrase = self.get_categories_with_word_phrase()

        response = self.client.get(
            self.get_list_endpoint(self.site.slug, query_kwargs={"contains": flag})
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == expected_count
        assert response_data["results"][0]["id"] == str(category_word.id)

    @pytest.mark.parametrize(
        "flag, expected_count", [("PHRASE", 1), ("phrase", 1), ("PhRaSe", 1)]
    )
    @pytest.mark.django_db
    def test_contains_phrase(self, flag, expected_count):
        # One category is added for a word and one for a phrase
        # Test should return only that entry which has the phrase associated with it

        _, _, category_word, category_phrase = self.get_categories_with_word_phrase()

        # Testing for PHRASE flag
        response = self.client.get(
            self.get_list_endpoint(self.site.slug, query_kwargs={"contains": flag})
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == expected_count
        assert response_data["results"][0]["id"] == str(category_phrase.id)

    @pytest.mark.django_db
    def test_contains_multiple(self):
        (
            word_entry,
            phrase_entry,
            category_word,
            category_phrase,
        ) = self.get_categories_with_word_phrase()
        category_both = ParentCategoryFactory(site=self.site)
        category_both.dictionary_entries.add(word_entry, phrase_entry)

        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug,
                query_kwargs={
                    "contains": f"{TypeOfDictionaryEntry.WORD}|{TypeOfDictionaryEntry.PHRASE}"
                },
            )
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 3

        ids_in_response = [
            str(response_obj["id"]) for response_obj in response_data["results"]
        ]
        actual_ids = [
            str(category_word.id),
            str(category_phrase.id),
            str(category_both.id),
        ]

        assert set(actual_ids) == set(ids_in_response)

    @pytest.mark.django_db
    def test_only_child_categories_contain_dictionary_entries(self):
        # There are r categories, a parent with 3 children, one just has a word which should show up ,
        # one of the children category has a phrase which should get filtered out, one has both a word and phrase
        # which should also show up. The parent does not has anything attached to it, so it should not show up
        word_entry_1 = DictionaryEntryFactory(site=self.site)
        phrase_entry_1 = DictionaryEntryFactory(
            site=self.site, type=TypeOfDictionaryEntry.PHRASE
        )

        parent_category = ParentCategoryFactory(site=self.site)
        child_category_word = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )
        child_category_phrase = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )
        child_category_both = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )

        child_category_word.dictionary_entries.add(word_entry_1)
        child_category_phrase.dictionary_entries.add(phrase_entry_1)
        child_category_both.dictionary_entries.add(word_entry_1, phrase_entry_1)

        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug,
                query_kwargs={"contains": TypeOfDictionaryEntry.WORD},
            )
        )
        response_data = json.loads(response.content)
        assert response.status_code == 200

        result_categories_count = response_data["count"]
        result_categories_ids = [
            category["id"] for category in response_data["results"]
        ]
        actual_categories_ids = [
            str(child_category_word.id),
            str(child_category_both.id),
        ]

        assert result_categories_count == 2
        assert set(actual_categories_ids) == set(result_categories_ids)

    @pytest.mark.django_db
    def test_both_children_and_parent_categories_contain_dictionary_entries(self):
        # There are 4 categories here, a parent category with 3 children, one just has a word which should show up,
        # one of the children category has a phrase which should get filtered out, one has both a word and phrase
        # which should also show up. The parent also has a word attached to it, so it should also show up
        word_entry_1 = DictionaryEntryFactory(site=self.site)
        word_entry_2 = DictionaryEntryFactory(site=self.site)
        phrase_entry_1 = DictionaryEntryFactory(
            site=self.site, type=TypeOfDictionaryEntry.PHRASE
        )

        parent_category = ParentCategoryFactory(site=self.site)
        child_category_word = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )
        child_category_phrase = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )
        child_category_both = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )

        parent_category.dictionary_entries.add(word_entry_1)
        child_category_word.dictionary_entries.add(word_entry_2)
        child_category_phrase.dictionary_entries.add(phrase_entry_1)
        child_category_both.dictionary_entries.add(word_entry_2, phrase_entry_1)

        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug,
                query_kwargs={"contains": TypeOfDictionaryEntry.WORD},
            )
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200

        result_parent_entry = response_data["results"][0]
        result_child_count = len(result_parent_entry["children"])
        result_child_ids = [child["id"] for child in result_parent_entry["children"]]
        actual_child_ids = [str(child_category_word.id), str(child_category_both.id)]

        assert result_parent_entry["id"] == str(parent_category.id)
        assert result_child_count == 2
        assert set(actual_child_ids) == set(result_child_ids)
