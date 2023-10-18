import pytest

from backend.search.utils.constants import VALID_DOCUMENT_TYPES
from backend.search.utils.query_builder_utils import (
    get_valid_category_id,
    get_valid_document_types,
    get_valid_domain,
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
