import json

import factory
import pytest
from factory.django import DjangoModelFactory
from rest_framework.test import APIClient

from backend.models.category import Category
from backend.models.constants import AppRole
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests.factories import (
    DictionaryEntryFactory,
    SiteFactory,
    UserFactory,
    get_app_admin,
)
from backend.tests.test_apis.base_api_test import BaseSiteContentApiTest


class ParentCategoryFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Category title %03d" % n)
    description = factory.Sequence(lambda n: "Category description %03d" % n)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)

    class Meta:
        model = Category


class ChildCategoryFactory(ParentCategoryFactory):
    parent = factory.SubFactory(ParentCategoryFactory)

    class Meta:
        model = Category


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

    @pytest.mark.django_db
    def test_contains_word(self):
        word_entry = DictionaryEntryFactory(site=self.site)
        category_word = ParentCategoryFactory(site=self.site)
        category_word.dictionary_entries.add(word_entry)

        # Testing for WORD flag
        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug, query_kwargs={"contains": TypeOfDictionaryEntry.WORD}
            )
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] > 0

        assert response_data["results"][0] == {
            "id": str(category_word.id),
            "title": category_word.title,
            "description": category_word.description,
            "children": [],
        }

        # Testing for PHRASE flag, should not return anything
        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug, query_kwargs={"contains": TypeOfDictionaryEntry.PHRASE}
            )
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 0

    @pytest.mark.django_db
    def test_contains_phrase(self):
        phrase_entry = DictionaryEntryFactory(
            site=self.site, type=TypeOfDictionaryEntry.PHRASE
        )
        category_phrase = ParentCategoryFactory(site=self.site)
        category_phrase.dictionary_entries.add(phrase_entry)

        # Testing for PHRASE flag
        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug, query_kwargs={"contains": TypeOfDictionaryEntry.PHRASE}
            )
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] > 0

        assert response_data["results"][0] == {
            "id": str(category_phrase.id),
            "title": category_phrase.title,
            "description": category_phrase.description,
            "children": [],
        }

        # Testing for WORD flag, should not return anything
        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug, query_kwargs={"contains": TypeOfDictionaryEntry.WORD}
            )
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] == 0

    @pytest.mark.django_db
    def test_contains_multiple(self):
        word_entry = DictionaryEntryFactory(site=self.site)
        phrase_entry = DictionaryEntryFactory(
            site=self.site, type=TypeOfDictionaryEntry.PHRASE
        )

        category_word = ParentCategoryFactory(site=self.site)
        category_phrase = ParentCategoryFactory(site=self.site)
        category_both = ParentCategoryFactory(site=self.site)

        category_word.dictionary_entries.add(word_entry)
        category_phrase.dictionary_entries.add(phrase_entry)
        category_both.dictionary_entries.add(word_entry, phrase_entry)

        # Testing for PHRASE flag
        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug,
                query_kwargs={
                    "contains": f"{TypeOfDictionaryEntry.WORD}|{TypeOfDictionaryEntry.PHRASE}"
                },
            )
        )
        response_data = json.loads(response.content)

        print(response_data)
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

        assert len(actual_ids) == len(ids_in_response)
        # Checking all ids match up
        difference = set(actual_ids) ^ set(ids_in_response)
        assert not difference


"""
Test for
1. Category 1 only contains word and return when asked for word, returns nothing for phrase
2. Contains both word and phrase, still returns when asked for word, returns also for phrase, and also for both
3. Contains only phrase, returns when asked for phrase, return nothing for word
4. Also consider cases when there are child categories as well

"""
