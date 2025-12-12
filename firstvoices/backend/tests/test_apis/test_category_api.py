import json

import pytest
from rest_framework.test import APIClient

from backend.models.category import Category
from backend.models.constants import Role, Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories
from backend.tests.factories import (
    CategoryFactory,
    ChildCategoryFactory,
    DictionaryEntryFactory,
    MembershipFactory,
    ParentCategoryFactory,
    SiteFactory,
    get_non_member_user,
)
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseUncontrolledSiteContentApiTest,
)
from backend.tests.utils import find_object_by_id


class TestCategoryEndpoints(BaseUncontrolledSiteContentApiTest):
    """
    End-to-end tests that the category endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:category-list"
    API_DETAIL_VIEW = "api:category-detail"
    TITLE = "Cool new title"
    model = Category

    def setup_method(self):
        self.client = APIClient()
        self.site = SiteFactory.create(visibility=Visibility.PUBLIC)

    def create_minimal_instance(self, site, visibility=None):
        return CategoryFactory(site=site)

    def get_expected_detail_response(self, instance, site):
        standard_fields = self.get_expected_entry_standard_fields(instance, site)
        return {
            **standard_fields,
            "description": instance.description,
            "children": [],
            "parent": None,
        }

    def assert_minimal_list_response(self, response, instance):
        """Override to assert the expected default number of categories"""
        assert response.status_code == 200
        response_data = json.loads(response.content)
        expected_count = Category.objects.filter(
            site=instance.site, parent__isnull=True
        ).count()
        assert response_data["count"] == expected_count

    def assert_minimal_list_response_no_email_access(self, response, instance):
        self.assert_minimal_list_response(response, instance)

    def get_valid_data(self, site=None):
        parent = CategoryFactory.create(site=site)

        return {
            "title": self.TITLE,
            "description": "Cool new description",
            "parent_id": str(parent.id),
        }

    def get_valid_data_with_nulls(self, site=None):
        return {
            "title": self.TITLE,
        }

    def get_valid_data_with_null_optional_charfields(self, site=None):
        return {
            "title": self.TITLE,
            "description": None,
        }

    def add_expected_defaults(self, data):
        return {**data, "parent": None, "description": ""}

    def assert_updated_instance(self, expected_data, actual_instance):
        assert actual_instance.title == expected_data["title"]
        assert actual_instance.description == expected_data["description"]
        if "parent_id" in expected_data:
            assert str(actual_instance.parent.id) == expected_data["parent_id"]
        else:
            assert actual_instance.parent == expected_data["parent"]

    def assert_update_response(self, expected_data, actual_response):
        assert actual_response["title"] == expected_data["title"]
        assert actual_response["description"] == expected_data["description"]
        if "parent_id" in expected_data:
            assert actual_response["parent"]["id"] == expected_data["parent_id"]
        else:
            assert actual_response["parent"] == expected_data["parent"]

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

    def create_dictionary_entry_with_category(
        self, site, entry_type=TypeOfDictionaryEntry.WORD, visibility=Visibility.PUBLIC
    ):
        entry = factories.DictionaryEntryFactory.create(
            site=site, visibility=visibility, type=entry_type
        )
        category = ParentCategoryFactory.create(site=site)
        category.dictionary_entries.add(entry)
        return entry, category

    def create_original_instance_for_patch(self, site):
        parent = factories.CategoryFactory.create(site=site, title="Title - Parent")
        return factories.CategoryFactory.create(
            site=site, title="Title", description="Description", parent=parent
        )

    def get_valid_patch_data(self, site=None):
        return {"title": "Title Updated"}

    def assert_patch_instance_original_fields(
        self, original_instance, updated_instance: Category
    ):
        assert updated_instance.id == original_instance.id
        assert updated_instance.description == original_instance.description
        assert updated_instance.parent == original_instance.parent

    def assert_patch_instance_updated_fields(self, data, updated_instance: Category):
        assert updated_instance.title == data["title"]

    def assert_update_patch_response(self, original_instance, data, actual_response):
        assert actual_response["id"] == str(original_instance.id)
        assert actual_response["title"] == data["title"]
        assert actual_response["description"] == original_instance.description
        assert actual_response["parent"]["id"] == str(original_instance.parent.id)
        assert actual_response["parent"]["title"] == original_instance.parent.title

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
                "url": f"http://testserver{self.get_detail_endpoint(child_category.id, self.site.slug)}",
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
        self.create_dictionary_entry_with_category(
            self.site,
            entry_type=TypeOfDictionaryEntry.PHRASE,
            visibility=Visibility.PUBLIC,
        )
        _, category_word = self.create_dictionary_entry_with_category(
            self.site,
            entry_type=TypeOfDictionaryEntry.WORD,
            visibility=Visibility.PUBLIC,
        )

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
        _, category_phrase = self.create_dictionary_entry_with_category(
            self.site,
            entry_type=TypeOfDictionaryEntry.PHRASE,
            visibility=Visibility.PUBLIC,
        )
        self.create_dictionary_entry_with_category(
            self.site,
            entry_type=TypeOfDictionaryEntry.WORD,
            visibility=Visibility.PUBLIC,
        )

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
        phrase_entry, category_phrase = self.create_dictionary_entry_with_category(
            self.site,
            entry_type=TypeOfDictionaryEntry.PHRASE,
            visibility=Visibility.PUBLIC,
        )
        word_entry, category_word = self.create_dictionary_entry_with_category(
            self.site,
            entry_type=TypeOfDictionaryEntry.WORD,
            visibility=Visibility.PUBLIC,
        )
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

    @pytest.mark.django_db
    def test_flat_list(self):
        parent_category_1 = ParentCategoryFactory.create(site=self.site)
        child_category_1 = ChildCategoryFactory.create(
            site=self.site, parent=parent_category_1
        )
        parent_category_2 = ParentCategoryFactory.create(site=self.site)
        child_category_2 = ChildCategoryFactory.create(
            site=self.site, parent=parent_category_2
        )

        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug,
                query_kwargs={"nested": False},
            )
        )

        response_data = json.loads(response.content)

        assert response.status_code == 200

        # verify that it is a flat list
        random_first_obj = response_data["results"][0]
        assert "children" not in random_first_obj.keys()
        assert "parent" in random_first_obj.keys()

        # verify that both pairs parent and child categories are present in response
        actual_parent_category_1_object = find_object_by_id(
            response_data["results"], parent_category_1.id
        )
        actual_child_category_1_object = find_object_by_id(
            response_data["results"], child_category_1.id
        )
        actual_parent_category_2_object = find_object_by_id(
            response_data["results"], parent_category_2.id
        )
        actual_child_category_2_object = find_object_by_id(
            response_data["results"], child_category_2.id
        )

        assert actual_parent_category_1_object is not None
        assert actual_child_category_1_object is not None
        assert actual_parent_category_2_object is not None
        assert actual_child_category_2_object is not None

    @pytest.mark.django_db
    def test_category_list_order(self):
        Category.objects.filter(site=self.site).delete()

        parent_category_1 = ParentCategoryFactory.create(site=self.site, title="b")
        parent_category_2 = ParentCategoryFactory.create(site=self.site, title="A")
        parent_category_3 = ParentCategoryFactory.create(site=self.site, title="C")
        child_category_1 = ChildCategoryFactory.create(
            site=self.site, parent=parent_category_1, title="e"
        )
        child_category_2 = ChildCategoryFactory.create(
            site=self.site, parent=parent_category_1, title="D"
        )
        child_category_3 = ChildCategoryFactory.create(
            site=self.site, parent=parent_category_1, title="F"
        )

        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug,
                query_kwargs={"nested": True},
            )
        )

        response_data = json.loads(response.content)

        assert response.status_code == 200

        actual_parent_category_1_object = find_object_by_id(
            response_data["results"], parent_category_1.id
        )
        actual_parent_category_2_object = find_object_by_id(
            response_data["results"], parent_category_2.id
        )
        actual_parent_category_3_object = find_object_by_id(
            response_data["results"], parent_category_3.id
        )
        actual_child_category_1_object = find_object_by_id(
            actual_parent_category_1_object["children"], child_category_1.id
        )
        actual_child_category_2_object = find_object_by_id(
            actual_parent_category_1_object["children"], child_category_2.id
        )
        actual_child_category_3_object = find_object_by_id(
            actual_parent_category_1_object["children"], child_category_3.id
        )

        # Check that the parent categories are ordered by title
        assert (
            response_data["results"].index(actual_parent_category_2_object)
            < response_data["results"].index(actual_parent_category_1_object)
            < response_data["results"].index(actual_parent_category_3_object)
        )

        # Check that the child categories are ordered by title within a parent category
        assert (
            actual_parent_category_1_object["children"].index(
                actual_child_category_2_object
            )
            < actual_parent_category_1_object["children"].index(
                actual_child_category_1_object
            )
            < actual_parent_category_1_object["children"].index(
                actual_child_category_3_object
            )
        )

    @pytest.mark.django_db
    def test_nested_list_with_parent_and_child(self):
        Category.objects.filter(site=self.site).delete()

        word_entry = DictionaryEntryFactory(site=self.site)

        parent_category_one = ParentCategoryFactory.create(
            site=self.site, title="Parent one"
        )
        child_category_one = ChildCategoryFactory.create(
            site=self.site, parent=parent_category_one, title="Child one of parent one"
        )
        parent_category_one.dictionary_entries.add(word_entry)
        child_category_one.dictionary_entries.add(word_entry)

        parent_category_two = ParentCategoryFactory.create(
            site=self.site, title="Parent two"
        )
        child_category_two = ChildCategoryFactory.create(
            site=self.site, parent=parent_category_two, title="Child one of parent two"
        )

        child_category_two.dictionary_entries.add(word_entry)

        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug,
                query_kwargs={"contains": TypeOfDictionaryEntry.WORD},
            )
        )
        response_data = json.loads(response.content)

        assert response.status_code == 200

        assert len(response_data["results"]) == 2

        assert response_data["results"][0]["id"] == str(child_category_two.id)
        assert response_data["results"][1]["id"] == str(parent_category_one.id)

        response_parent_category_one = response_data["results"][1]
        assert len(response_parent_category_one["children"]) == 1
        assert response_parent_category_one["children"][0]["id"] == str(
            child_category_one.id
        )

    @pytest.mark.django_db
    def test_nested_lists_with_contains_parameter_returns_distinct_categories(self):
        Category.objects.filter(site=self.site).delete()

        parent_category = ParentCategoryFactory.create(site=self.site, title="Parent")
        child_category = ChildCategoryFactory.create(
            site=self.site, parent=parent_category, title="Child"
        )

        word_entry_1 = DictionaryEntryFactory(site=self.site)
        word_entry_2 = DictionaryEntryFactory(site=self.site)

        parent_category.dictionary_entries.add(word_entry_1)
        child_category.dictionary_entries.add(word_entry_1)
        child_category.dictionary_entries.add(word_entry_2)

        response = self.client.get(
            self.get_list_endpoint(
                self.site.slug,
                query_kwargs={"contains": TypeOfDictionaryEntry.WORD},
            )
        )
        response_data = json.loads(response.content)
        results = response_data["results"]

        assert response.status_code == 200
        assert len(results) == 1
        assert results[0]["id"] == str(parent_category.id)

        assert len(results[0]["children"]) == 1
        assert results[0]["children"][0]["id"] == str(child_category.id)

    @pytest.mark.django_db
    def test_flat_list_parentTitle_basic(self):
        parent = ParentCategoryFactory.create(site=self.site, title="Animal")
        child = ChildCategoryFactory.create(
            site=self.site, parent=parent, title="Lizards"
        )

        resp = self.client.get(
            self.get_list_endpoint(
                self.site.slug,
                query_kwargs={"nested": False},
            )
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)

        assert all("children" not in obj for obj in data["results"])

        assert all("parent" in obj and "parentTitle" in obj for obj in data["results"])

        parent_obj = find_object_by_id(data["results"], parent.id)
        child_obj = find_object_by_id(data["results"], child.id)
        assert parent_obj is not None and child_obj is not None

        assert parent_obj["parent"] is None
        assert parent_obj["parentTitle"] == ""

        assert child_obj["parent"] == str(parent.id)
        assert child_obj["parentTitle"] == parent.title
