import pytest
from django.db.utils import DataError

from firstvoices.backend.models.dictionary import TITLE_MAX_LENGTH, DictionaryEntry
from firstvoices.backend.tests.factories import SiteFactory
from firstvoices.backend.tests.utils import generate_string


class TestDictionaryModel:
    """Test for dictionary entry model"""

    def test_max_length_success(self, db):
        site = SiteFactory.create()
        entry_title_valid = generate_string(TITLE_MAX_LENGTH - 1)

        entry = DictionaryEntry(title=entry_title_valid, type="WORD", site=site)
        entry.save()

        fetched_entry = DictionaryEntry.objects.get(title=entry_title_valid)
        assert fetched_entry.title == entry_title_valid

    def test_max_length_failure(self, db):
        site = SiteFactory.create()
        entry_title_invalid = generate_string(TITLE_MAX_LENGTH + 1)

        with pytest.raises(DataError):
            entry_to_fail = DictionaryEntry(
                title=entry_title_invalid, type="WORD", site=site
            )
            entry_to_fail.save()

    def test_truncating_field_custom_order_no_truncation(self, db):
        site = SiteFactory.create()
        custom_order_string_length = TITLE_MAX_LENGTH // 2
        custom_order_string = generate_string(custom_order_string_length)
        entry = DictionaryEntry(
            title="Entry 1", type="WORD", custom_order=custom_order_string, site=site
        )
        entry.save()
        fetched_entry = DictionaryEntry.objects.get(title="Entry 1")
        assert fetched_entry.title == "Entry 1"
        assert len(fetched_entry.custom_order) == custom_order_string_length

    def test_truncating_field_custom_order_truncation(self, db):
        """Verify if the custom order field of dictionary entry is removing extra characters after max length"""

        site = SiteFactory.create()
        custom_order_string = generate_string(2 * TITLE_MAX_LENGTH)

        entry = DictionaryEntry(
            title="Entry 1", type="WORD", custom_order=custom_order_string, site=site
        )
        entry.save()
        fetched_entry = DictionaryEntry.objects.get(title="Entry 1")
        assert fetched_entry.title == "Entry 1"
        assert len(fetched_entry.custom_order) == TITLE_MAX_LENGTH

    def test_truncating_field_custom_order_whitespace(self, db):
        """Verify if the custom order field is trimming whitepsace characters as expected."""

        site = SiteFactory.create()
        custom_order_string_length = 50
        custom_order_string = generate_string(50)
        custom_order_string = (
            " " * 10 + custom_order_string + " " * 10
        )  # Adding whitespace characters before and after

        entry = DictionaryEntry(
            title="Entry 1", type="WORD", custom_order=custom_order_string, site=site
        )
        entry.save()
        fetched_entry = DictionaryEntry.objects.get(title="Entry 1")
        assert fetched_entry.title == "Entry 1"
        assert len(fetched_entry.custom_order) == custom_order_string_length

    def test_truncating_field_custom_order_only_whitespace_trimming(self, db):
        """Verify that the field is removing whitespace first and then any characters if required."""

        site = SiteFactory.create()
        custom_order_string_length = TITLE_MAX_LENGTH - 5
        custom_order_string = generate_string(custom_order_string_length)
        custom_order_string_with_whitespace = (
            " " * 10 + custom_order_string
        )  # Adding whitespace characters before

        entry = DictionaryEntry(
            title="Entry 1",
            type="WORD",
            custom_order=custom_order_string_with_whitespace,
            site=site,
        )
        entry.save()
        fetched_entry = DictionaryEntry.objects.get(title="Entry 1")
        assert fetched_entry.title == "Entry 1"
        assert len(fetched_entry.custom_order) == custom_order_string_length
        assert fetched_entry.custom_order == custom_order_string
