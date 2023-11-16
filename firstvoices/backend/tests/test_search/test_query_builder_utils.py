import pytest

from backend.models.constants import Visibility
from backend.search.utils.constants import VALID_DOCUMENT_TYPES
from backend.search.utils.query_builder_utils import (
    get_valid_category_id,
    get_valid_document_types,
    get_valid_domain,
    get_valid_sort,
    get_valid_visibility,
)
from backend.tests import factories


class TestValidDocumentTypes:
    @pytest.mark.parametrize(
        "input_types, expected_types",
        [
            ("word", ["word"]),
            ("word, song, audio", ["word", "song", "audio"]),
            (" word,    song, audio ", ["word", "song", "audio"]),
            ("invalid_type_1, invalid_type_2", None),
            ("song, invalid_type, image, invalid_type_2", ["song", "image"]),
            ("word, word, phrase", ["word", "phrase"]),
            ("WORD, PhRasE, Audio", ["word", "phrase", "audio"]),
        ],
    )
    def test_mixed_input_doc_types(self, input_types, expected_types):
        # test for all caps, mixed cases, invalid types, and combination of invalid and valid types
        actual_types = get_valid_document_types(input_types)
        assert expected_types == actual_types

    def test_empty_input_return_all_types(self):
        actual_types = get_valid_document_types("")
        assert VALID_DOCUMENT_TYPES == actual_types


class TestValidDomains:
    @pytest.mark.parametrize(
        "input_domain, expected_domain",
        [
            ("TRANSLATION", "translation"),
            ("LANGUAGE", "language"),
            ("both", "both"),
            (" ", "both"),
        ],
    )
    def test_valid_inputs(self, input_domain, expected_domain):
        actual_domain = get_valid_domain(input_domain)
        assert expected_domain == actual_domain

    def test_invalid_input(self):
        actual_domain = get_valid_domain("bananas")
        assert actual_domain is None


@pytest.mark.django_db
class TestValidCategory:
    def setup_method(self):
        self.site = factories.SiteFactory()
        self.category = factories.ParentCategoryFactory(site=self.site)

    def test_valid_input(self):
        expected_category_id = self.category.id
        actual_category_id = get_valid_category_id(self.site, self.category.id)

        assert expected_category_id == actual_category_id

    def test_invalid_input(self):
        actual_category_id = get_valid_category_id(self.site, "not_real_category")

        assert actual_category_id is None


class TestValidVisibility:
    @pytest.mark.parametrize(
        "input_visibility, expected_visibility",
        [
            ("Team", [Visibility.TEAM]),
            ("TeAm", [Visibility.TEAM]),
            ("Members", [Visibility.MEMBERS]),
            ("members", [Visibility.MEMBERS]),
            ("Public", [Visibility.PUBLIC]),
            ("invalid, Team", [Visibility.TEAM]),
            ("Team, Members", [Visibility.TEAM, Visibility.MEMBERS]),
            (
                "Team, Members, Public",
                [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC],
            ),
        ],
    )
    def test_valid_inputs(self, input_visibility, expected_visibility):
        actual_visibility = get_valid_visibility(input_visibility)
        for value in actual_visibility:
            assert value in expected_visibility

    def test_invalid_input(self):
        actual_visibility = get_valid_visibility("bananas")
        assert actual_visibility is None


class TestValidSort:
    @pytest.mark.parametrize(
        "input_sort, expected_sort",
        [
            ("created", ("created", False)),
            ("modified", ("modified", False)),
            ("title", ("title", False)),
            ("crEaTed", ("created", False)),
            ("MODIFIED", ("modified", False)),
            ("TiTlE", ("title", False)),
            ("created_desc", ("created", True)),
            ("modified_desc", ("modified", True)),
            ("title_desc", ("title", True)),
            ("crEaTed_desC", ("created", True)),
            ("MODIFIED_DeSc", ("modified", True)),
            ("TiTlE_DESC", ("title", True)),
        ],
    )
    def test_valid_inputs(self, input_sort, expected_sort):
        actual_sort = get_valid_sort(input_sort)
        assert actual_sort == expected_sort

    def test_invalid_input(self):
        actual_sort, descending = get_valid_sort("bananas")
        assert actual_sort is None
        assert descending is None
