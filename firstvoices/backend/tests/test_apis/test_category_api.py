import json

import pytest
from rest_framework.test import APIClient

from backend.models.category import Category
from backend.models.constants import AppRole, Role, Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests.factories import (
    CategoryFactory,
    ChildCategoryFactory,
    DictionaryEntryFactory,
    MembershipFactory,
    ParentCategoryFactory,
    SiteFactory,
    get_app_admin,
    get_non_member_user,
)
from backend.tests.test_apis.base_api_test import BaseUncontrolledSiteContentApiTest


class TestCategoryEndpoints(BaseUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the category endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:category-list"
    API_DETAIL_VIEW = "api:category-detail"
    model = Category

    def setup_method(self):
        self.client = APIClient()
        self.user = get_app_admin(AppRole.STAFF)
        self.client.force_authenticate(user=self.user)
        self.site = SiteFactory.create()

    def create_minimal_instance(self, site, visibility=None):
        return CategoryFactory(site=site)

    def get_expected_detail_response(self, instance, site):
        return {
            "url": f"http://testserver{self.get_detail_endpoint(instance.id, instance.site.slug)}",
            "id": str(instance.id),
            "title": instance.title,
            "description": instance.description,
            "children": [],
            "parent": None,
        }

    def get_valid_data(self, site=None):
        parent = CategoryFactory.create(site=site)

        return {
            "title": "Cool new title",
            "description": "Cool new description",
            "parent_id": str(parent.id),
        }

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.description == expected_data["description"]
        assert str(actual_instance.parent.id) == expected_data["parent_id"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["description"] == expected_data["description"]
        assert actual_response["parent"]["id"] == expected_data["parent_id"]

    def assert_created_instance(self, pk, data):
        instance = Category.objects.get(pk=pk)
        return self.assert_updated_instance(data, instance)

    def assert_created_response(self, expected_data, actual_response):
        return self.assert_update_response(expected_data, actual_response)

    def add_related_objects(self, instance):
        # no related objects to add
        pass

    def assert_related_objects_deleted(self, instance):
        # no related objects to delete
        pass

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
        Skipping, since categories are always generated when a site is initialized.
        """
        pass

    @pytest.mark.django_db
    def test_list_minimal(self):
        """
        Skipping, since categories are always generated when a site is initialized.
        """
        pass

    @pytest.mark.parametrize("role", Role)
    @pytest.mark.django_db
    def test_list_member_access(self, role):
        """
        Overriding to assert non-empty list, since categories are always added when a site is created.
        """
        site = SiteFactory.create(visibility=Visibility.MEMBERS)
        user = get_non_member_user()
        MembershipFactory.create(user=user, site=site, role=role)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 15

    @pytest.mark.django_db
    def test_list_team_access(self):
        """
        Overriding to assert non-empty list, since categories are always added when a site is created.
        """
        site = SiteFactory.create(visibility=Visibility.TEAM)
        user = get_non_member_user()
        MembershipFactory.create(user=user, site=site, role=Role.ASSISTANT)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.get_list_endpoint(site.slug))

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["count"] == 15

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
        assert "url" in category_json
        assert "id" in category_json
        assert "title" in category_json
        assert "children" in category_json
        assert isinstance(category_json["children"], list)
        assert "description" in category_json

    @pytest.mark.django_db
    def test_detail_has_children(self):
        parent_category = ParentCategoryFactory.create(site=self.site)
        child_category = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )
        detail_endpoint = self.get_detail_endpoint(parent_category.id, self.site.slug)
        response = self.client.get(detail_endpoint)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["children"] == [
            {
                "url": f"http://testserver{self.get_detail_endpoint(child_category.id, child_category.site.slug)}",
                "id": str(child_category.id),
                "title": child_category.title,
                "description": child_category.description,
            }
        ]

    @pytest.mark.django_db
    def test_detail_has_parent(self):
        parent_category = ParentCategoryFactory.create(site=self.site)
        child_category = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )

        detail_endpoint = self.get_detail_endpoint(child_category.id, self.site.slug)

        response = self.client.get(detail_endpoint)
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["parent"] == {
            "id": str(parent_category.id),
            "title": parent_category.title,
            "url": f"http://testserver{self.get_detail_endpoint(parent_category.id, parent_category.site.slug)}",
        }

    @pytest.mark.django_db
    def test_detail_404(self):
        wrong_endpoint = self.get_detail_endpoint("54321", self.site.slug)
        response = self.client.get(wrong_endpoint)
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "invalid_flags, expected_count",
        [
            ("invalid_value", 0),
            ("word|invalid_Value", 1),
            ("phrase|word|invalid_Value", 2),
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

        _, _, category_word, _ = self.get_categories_with_word_phrase()

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

        _, _, _, category_phrase = self.get_categories_with_word_phrase()

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

        response_ids = [
            str(response_obj["id"]) for response_obj in response_data["results"]
        ]
        expected_ids = [
            str(category_word.id),
            str(category_phrase.id),
            str(category_both.id),
        ]

        assert set(expected_ids) == set(response_ids)

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

        response_categories_count = response_data["count"]
        response_ids = [category["id"] for category in response_data["results"]]
        expected_ids = [
            str(child_category_word.id),
            str(child_category_both.id),
        ]

        assert response_categories_count == 2
        assert set(expected_ids) == set(response_ids)

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

        response_parent_entry = response_data["results"][0]
        response_child_category_count = len(response_parent_entry["children"])
        response_ids = [child["id"] for child in response_parent_entry["children"]]
        expected_ids = [str(child_category_word.id), str(child_category_both.id)]

        assert response_parent_entry["id"] == str(parent_category.id)
        assert response_child_category_count == 2
        assert set(expected_ids) == set(response_ids)
