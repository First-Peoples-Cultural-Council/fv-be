import pytest

from backend.search.utils.constants import VALID_DOCUMENT_TYPES
from backend.search.utils.query_builder_utils import (
    get_valid_document_types,
    get_valid_domain,
)


class TestValidDocumentTypes:
    @pytest.mark.parametrize(
        "input_types, expected_types",
        [
            ("WORDS", ["words"]),
            ("PHRASES", ["phrases"]),
            ("PHRASES, WORDS", ["phrases", "words"]),
            ("WORDS, PHRASES", ["words", "phrases"]),
            ("WordS, PhrASes", ["words", "phrases"]),
            ("xyz_type", None),
            ("memory, WORDS", ["words"]),
            ("storage, PHRASES, WORDS", ["phrases", "words"]),
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
            ("english", "english"),
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
