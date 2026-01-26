from itertools import product

import pytest
from rest_framework import serializers
from utils.export_utils import expand_row, get_first_seen_keys, get_max_lengths

from backend.serializers.utils.import_job_utils import check_required_headers
from backend.tasks.import_job_tasks import clean_csv
from backend.tests.utils import get_batch_import_test_dataset
from backend.utils.character_utils import ArbSorter, CustomSorter, nfc


class TestCharacterUtils:
    chars = list("abcqwertyuiop")
    extra_chars = list("sfghjklzxvnm0987654321")
    non_char = "d"

    def test_arb_sorter_values(self):
        sorter = ArbSorter(order=self.chars)
        assert sorter.word_as_values("abc") == [0, 1, 2]
        assert sorter.word_as_values("d") == [10100]
        assert sorter.word_as_values("q") < sorter.word_as_values("p")

    def test_arb_sorter_ignorable(self):
        sorter = ArbSorter(order=self.chars, ignorable=list("/"))
        assert sorter.word_as_values("/") == []
        assert sorter.word_as_values("a/b/c") == [0, 1, 2]

    def test_custom_sorter_space(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.custom_sort_char(0) == " "

    def test_custom_sorter_base_chars(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.custom_sort_char(1) == "!"
        assert sorter.custom_sort_char(2) == "#"
        assert sorter.custom_sort_char(3) == "$"
        assert len(sorter.custom_order) == len(self.chars) + 1
        assert isinstance(sorter.custom_sort_char(len(self.chars)), str)
        assert sorter.custom_sort_char(len(self.chars) + 1) is None

    def test_custom_sorter_avoid_escape_chars(self):
        many_chars = self.chars + self.extra_chars
        sorter = CustomSorter(order=many_chars)
        assert '"' not in sorter.word_as_sort_string("".join(many_chars))
        assert "\\" not in sorter.word_as_sort_string("".join(many_chars))

    def test_custom_sorter_long_alphabet(self):
        double_chars = [a + b for (a, b) in product(self.chars, self.chars)]
        alph = self.chars + double_chars
        sorter = CustomSorter(order=alph)
        assert len(sorter.custom_order) == len(alph) + 1
        assert isinstance(sorter.custom_sort_char(150), str)

    def test_custom_sorter_oov_char(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.out_of_vocab_flag == "⚑"
        assert sorter.custom_sort_char(len(self.chars) + 1) is None
        assert sorter.custom_sort_char(10000 + ord("d")) == "⚑d"

    def test_custom_sort_string_basic(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.word_as_sort_string("abc") == "!#$"
        assert sorter.word_as_sort_string("ab c") == "!# $"
        assert sorter.word_as_sort_string("a") != sorter.word_as_sort_string("A")
        assert sorter.word_as_sort_string("d") == "⚑d"
        assert sorter.word_as_sort_string("abcd") == "!#$⚑d"
        assert sorter.word_as_sort_string("qwe") < sorter.word_as_sort_string("iop")

    def test_custom_sort_string_multichar(self):
        sorter = CustomSorter(order=["c", "ch", "a", "aa"])
        assert sorter.word_as_sort_string("ch") == sorter.custom_sort_char(2)
        assert sorter.word_as_sort_string("aa") == sorter.custom_sort_char(4)

    def test_custom_sort_string_ignorable(self):
        sorter = CustomSorter(order=["a", "aa", "c", "ch"], ignorable=list("/-"))
        assert sorter.word_as_sort_string("/-//") == ""
        assert sorter.word_as_sort_string("a/a") != sorter.custom_sort_char(2)
        assert sorter.word_as_sort_string("a/a") == sorter.custom_sort_char(1) * 2
        assert sorter.word_as_sort_string("c-h") == "$⚑h"

    def test_word_as_chars_basic(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.word_as_chars("abc") == ["a", "b", "c"]
        assert sorter.word_as_chars("ab c") == ["a", "b", " ", "c"]
        assert sorter.word_as_chars("abcd") == ["a", "b", "c", "d"]
        assert sorter.word_as_chars(" q we ") == [" ", "q", " ", "w", "e", " "]

    def test_word_as_chars_multichar(self):
        sorter = CustomSorter(order=["c", "ch", "a", "aa"])
        assert sorter.word_as_chars("ch") == ["ch"]
        assert sorter.word_as_chars("aa") == ["aa"]
        assert sorter.word_as_chars("cch") == ["c", "ch"]
        assert sorter.word_as_chars("aach") == ["aa", "ch"]

    def test_word_as_chars_special_characters(self):
        sorter = CustomSorter(order=["a", "aa", "c", "ch.", "h", "x-", "y", "-", "."])
        assert sorter.word_as_chars("x-y") == ["x-", "y"]
        assert sorter.word_as_chars("cch..") == ["c", "ch.", "."]
        assert sorter.word_as_chars("c-h") == ["c", "-", "h"]

    def test_nfc_normalization(self):
        expected_str = "ááááá"
        input_str = "ááááá"
        assert nfc(input_str) == expected_str


class TestValidateRequiredHeaders:
    def test_valid_headers_present(self):
        input_headers = ["title", "type", "description", "notes"]
        assert check_required_headers(input_headers)

    @pytest.mark.parametrize(
        "input_headers",
        [["type", "note"], ["title", "audio"], ["note", "audio"]],
    )
    def test_valid_headers_missing(self, input_headers):
        with pytest.raises(serializers.ValidationError):
            check_required_headers(input_headers)


class TestCleanCsv:
    def test_valid_columns(self):
        data = get_batch_import_test_dataset("all_valid_columns.csv")
        accepted_headers, invalid_headers, data = clean_csv(data)

        # All headers should be present in accepted headers
        assert len(accepted_headers) == len(data.headers)
        assert invalid_headers == []

    def test_unknown_columns(self):
        data = get_batch_import_test_dataset("unknown_columns.csv")
        accepted_headers, invalid_headers, cleaned_data = clean_csv(data)

        assert len(accepted_headers) == 3
        assert "abc" in invalid_headers
        assert "xyz" in invalid_headers

        assert "title" in cleaned_data.headers
        assert "abc" not in cleaned_data.headers
        assert "xyz" not in cleaned_data.headers

    def test_out_of_range_variations(self):
        data = get_batch_import_test_dataset("out_of_range_variations.csv")
        accepted_headers, invalid_headers, _ = clean_csv(data)

        assert len(accepted_headers) == 7
        assert "translation_2" in accepted_headers
        assert "note_2" in accepted_headers

        assert "translation_6" in invalid_headers
        assert "translation_8" in invalid_headers
        assert "note_6" in invalid_headers
        assert "note_99" in invalid_headers


class TestCustomCsvRenderer:
    def test_get_max_lengths(self):
        rows = [
            {
                "translations": ["translation_1", "translation_2"],
                "notes": ["note_1", "note_2", "note_3"],
            },
            {
                "translations": ["translation_1"],
                "notes": [
                    "note_1",
                    "note_2",
                ],
            },
        ]
        fields = ["translations", "notes"]
        max_lengths = get_max_lengths(rows, fields)
        assert max_lengths["translations"] == 2
        assert max_lengths["notes"] == 3

    def test_get_first_seen_keys(self):
        rows = [
            {
                "id": 123,
                "title": "abc",
                "translations": ["translation_1", "translation_2"],
            },
            {"id": 456, "notes": ["note_1", "note_2"]},
        ]
        assert get_first_seen_keys(rows) == [
            "id",
            "title",
            "translations",
            "notes",
        ]

    def test_expand_rows(self):
        row = {
            "id": 123,
            "title": "abc",
            "translations": ["translation_1", "translation_2", "translation_3"],
        }
        flatten_fields = {"translations": "translation"}
        max_lengths = get_max_lengths([row], flatten_fields.keys())

        expanded_headers = [
            "id",
            "title",
            "translation",
            "translation_2",
            "translation_3",
        ]
        expanded_row = expand_row(row, expanded_headers, flatten_fields, max_lengths)
        assert expanded_row["id"] == 123
        assert expanded_row["title"] == "abc"
        assert expanded_row["translation"] == "translation_1"
        assert expanded_row["translation_2"] == "translation_2"
        assert expanded_row["translation_3"] == "translation_3"
