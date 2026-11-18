from datetime import date
from itertools import product

import pytest
import requests
from rest_framework import serializers

from backend.serializers.utils.import_job_utils import check_required_headers
from backend.tasks.import_job_tasks import clean_csv
from backend.tests.utils import get_batch_import_test_dataset
from backend.utils.character_utils import ArbSorter, CustomSorter, nfc
from backend.utils.export_utils import expand_row, get_first_seen_keys, get_max_lengths
from backend.utils.matomo_utils import get_monthly_visitors
from backend.views.exceptions import (
    MatomoConfigurationError,
    MatomoError,
    MatomoTimeoutError,
)


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

        assert "translation_11" in invalid_headers
        assert "translation_12" in invalid_headers
        assert "note_20" in invalid_headers
        assert "note_99" in invalid_headers


class TestExportUtils:
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


class TestMatomoUtils:
    @pytest.fixture
    def matomo_post(self, settings, mocker):
        settings.MATOMO_API_URL = "https://analytics.example.com/index.php"
        settings.MATOMO_AUTH_TOKEN = "test-token"
        settings.MATOMO_SITE_ID = "4"
        settings.MATOMO_TRACKED_SITE_URL = "https://www.example.com/"
        post = mocker.patch("backend.utils.matomo_utils.requests.post")
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "nb_visits": 590,
            "nb_uniq_visitors": 364,
        }
        return post

    def test_get_monthly_visitors(self, matomo_post):
        metrics = get_monthly_visitors("test_site", date(2026, 10, 1))

        assert metrics == {"total_visits": 590, "unique_visitors": 364}
        matomo_post.assert_called_once_with(
            "https://analytics.example.com/index.php",
            data={
                "module": "API",
                "method": "VisitsSummary.get",
                "format": "JSON",
                "idSite": 4,
                "period": "month",
                "date": "2026-10-01",
                "segment": (
                    "pageUrl==https%3A%2F%2Fwww.example.com%2Ftest_site,"
                    "pageUrl=^https%3A%2F%2Fwww.example.com%2Ftest_site%2F"
                ),
                "token_auth": "test-token",
            },
            timeout=(5, 15),
            allow_redirects=False,
        )

    def test_zero_visitors(self, matomo_post):
        matomo_post.return_value.json.return_value = {
            "nb_visits": 0,
            "nb_uniq_visitors": 0,
        }

        metrics = get_monthly_visitors("test_site", date(2026, 10, 1))

        assert metrics == {"total_visits": 0, "unique_visitors": 0}

    @pytest.mark.parametrize(
        "setting_name, value",
        [
            ("MATOMO_API_URL", None),
            ("MATOMO_AUTH_TOKEN", ""),
            ("MATOMO_SITE_ID", None),
            ("MATOMO_TRACKED_SITE_URL", ""),
            ("MATOMO_SITE_ID", "not-an-id"),
            ("MATOMO_API_URL", "http://analytics.example.com/index.php"),
            ("MATOMO_TRACKED_SITE_URL", "https://www.example.com/lilwat"),
        ],
    )
    def test_invalid_configuration(self, setting_name, value, matomo_post, settings):
        setattr(settings, setting_name, value)

        with pytest.raises(MatomoConfigurationError):
            get_monthly_visitors("test_site", date(2026, 10, 1))

        matomo_post.assert_not_called()

    @pytest.mark.parametrize("status_code", [302, 401, 500])
    def test_matomo_http_error(self, status_code, matomo_post):
        matomo_post.return_value.status_code = status_code

        with pytest.raises(MatomoError):
            get_monthly_visitors("test_site", date(2026, 10, 1))

    def test_matomo_api_error(self, matomo_post):
        # Matomo also reports API errors in responses with HTTP status 200.
        matomo_post.return_value.json.return_value = {
            "result": "error",
            "message": "The authentication token is not valid.",
        }

        with pytest.raises(MatomoError) as error:
            get_monthly_visitors("test_site", date(2026, 10, 1))

        assert error.value.detail == MatomoError.default_detail

    @pytest.mark.parametrize("report", [{}, [], {"nb_visits": "invalid"}])
    def test_invalid_report(self, report, matomo_post):
        matomo_post.return_value.json.return_value = report

        with pytest.raises(MatomoError):
            get_monthly_visitors("test_site", date(2026, 10, 1))

    def test_invalid_json(self, matomo_post):
        matomo_post.return_value.json.side_effect = ValueError

        with pytest.raises(MatomoError):
            get_monthly_visitors("test_site", date(2026, 10, 1))

    def test_matomo_timeout(self, matomo_post):
        matomo_post.side_effect = requests.Timeout

        with pytest.raises(MatomoTimeoutError):
            get_monthly_visitors("test_site", date(2026, 10, 1))

    def test_matomo_connection_error(self, matomo_post):
        matomo_post.side_effect = requests.ConnectionError

        with pytest.raises(MatomoError):
            get_monthly_visitors("test_site", date(2026, 10, 1))
