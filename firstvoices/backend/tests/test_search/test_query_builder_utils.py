import pytest

from backend.search.utils.constants import VALID_DOCUMENT_TYPES
from backend.search.utils.query_builder_utils import get_valid_document_types


class TestValidDocumentTypes:
    @pytest.mark.parametrize(
        "input_types, expected_types",
        [
            ("WORDS", ["words"]),
            ("PHRASES", ["phrases"]),
            ("PHRASES, WORDS", ["phrases", "words"]),
            ("WORDS, PHRASES", ["words", "phrases"]),
            ("WordS, PhrASes", ["words", "phrases"]),
        ],
    )
    def test_doc_type_mixed_cases(self, input_types, expected_types):
        actual_types = get_valid_document_types(input_types)
        assert expected_types == actual_types

    @pytest.mark.parametrize(
        "input_types, expected_types",
        [
            ("xyz_type", []),
            ("memory, WORDS", ["words"]),
            ("storage, PHRASES, WORDS", ["phrases", "words"]),
        ],
    )
    def test_ignore_invalid_types(self, input_types, expected_types):
        actual_types = get_valid_document_types(input_types)
        assert expected_types == actual_types

    def test_empty_input_return_all_types(self):
        actual_types = get_valid_document_types("")
        assert VALID_DOCUMENT_TYPES == actual_types
