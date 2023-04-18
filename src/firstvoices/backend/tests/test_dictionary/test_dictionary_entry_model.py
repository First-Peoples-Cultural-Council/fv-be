import pytest
from django.db.utils import DataError

from firstvoices.backend.models.constants import DICTIONARY_MODELS_TITLE_MAX_LENGTH
from firstvoices.backend.models.dictionary import DictionaryEntry
from firstvoices.backend.tests.factories import SiteFactory
from firstvoices.backend.tests.utils import generate_string


class TestDictionaryModel:
    """Test for dictionary entry model"""

    def test_max_length_enforced(self, db):
        site = SiteFactory.create()
        entry_title_valid = generate_string(DICTIONARY_MODELS_TITLE_MAX_LENGTH - 1)
        entry_title_invalid = generate_string(DICTIONARY_MODELS_TITLE_MAX_LENGTH + 1)

        entry_to_pass = DictionaryEntry(title=entry_title_valid, type="WORD", site=site)
        entry_to_pass.save()

        with pytest.raises(DataError):
            entry_to_fail = DictionaryEntry(
                title=entry_title_invalid, type="WORD", site=site
            )
            entry_to_fail.save()

    def test_truncate_string_custom_order_field(self, db):
        """Verify if the custom order field of dictionary entry is removing extra characters after max length"""

        site = SiteFactory.create()

        custom_order_string = generate_string(2 * DICTIONARY_MODELS_TITLE_MAX_LENGTH)

        entry = DictionaryEntry(
            title="Entry 1", type="WORD", custom_order=custom_order_string, site=site
        )
        entry.save()
        fetched_entry = DictionaryEntry.objects.get(title="Entry 1")
        assert len(fetched_entry.custom_order) == DICTIONARY_MODELS_TITLE_MAX_LENGTH
