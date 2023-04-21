import pytest
from backend.models.characters import Alphabet
from backend.models.dictionary import TITLE_MAX_LENGTH, DictionaryEntry
from backend.tests.factories import (
    AlphabetFactory,
    ControlledSiteContentFactory,
    SiteFactory,
)
from backend.tests.utils import generate_string
from django.core.management import call_command
from django.db.utils import DataError


class TestDictionaryEntryModel:
    """Test for dictionary entry model.
    Note related to tests related to custom_order field: if the title is made up of unknown characters, as in the case
    of all the following tests, the custom_order field contains all the unknown characters and a flag for each unknown
    character, i.e. length of custom order field should be double that of title field.
    """

    @pytest.fixture
    def g2p_db_setup(self, django_db_blocker):
        """Required as to create a dictionary entry, we need alphabets and g2p config for alphabets."""
        with django_db_blocker.unblock():
            call_command("loaddata", "default_g2p_config.json")

    def test_max_length_success(self, db, g2p_db_setup):
        site = SiteFactory.create()
        entry_title_valid = generate_string(TITLE_MAX_LENGTH - 1)

        entry = DictionaryEntry(title=entry_title_valid, type="WORD", site=site)
        entry.save()

        fetched_entry = DictionaryEntry.objects.get(title=entry_title_valid)
        assert fetched_entry.title == entry_title_valid

    def test_max_length_failure(self, db, g2p_db_setup):
        site = SiteFactory.create()
        entry_title_invalid = generate_string(TITLE_MAX_LENGTH + 1)

        with pytest.raises(DataError):
            entry_to_fail = DictionaryEntry(
                title=entry_title_invalid, type="WORD", site=site
            )
            entry_to_fail.save()

    def test_truncating_field_custom_order_no_truncation(self, db, g2p_db_setup):
        site = SiteFactory.create()
        entry_title_length = 10
        entry_title_string = generate_string(entry_title_length)
        entry = DictionaryEntry(title=entry_title_string, type="WORD", site=site)
        entry.save()
        fetched_entry = DictionaryEntry.objects.get(title=entry_title_string)
        assert fetched_entry.title == entry_title_string
        assert len(fetched_entry.custom_order) == 20

    def test_truncating_field_custom_order_truncation(self, db, g2p_db_setup):
        """Verify if the custom order field of dictionary entry is removing extra characters after max length.
        Testing for the maximum length case in this test
        """

        site = SiteFactory.create()
        long_title = generate_string(TITLE_MAX_LENGTH)

        entry = DictionaryEntry(title=long_title, type="WORD", site=site)
        entry.save()
        fetched_entry = DictionaryEntry.objects.get(title=long_title)
        assert fetched_entry.title == long_title
        assert len(fetched_entry.custom_order) == TITLE_MAX_LENGTH

    def test_truncating_field_custom_order_whitespace(self, db, g2p_db_setup):
        """Verify if the custom order field is does not retain any leading or trailing whitepsaces. Though spaces are
        mapped 1-1 in custom order field, The title field also removes any whitesspace before saving an entry.
        """

        site = SiteFactory.create()
        title_length = 50
        entry_title = generate_string(title_length)
        entry_title_with_whitespace = (
            " " * 10 + entry_title + " " * 10
        )  # Adding whitespace characters before and after

        entry = DictionaryEntry(
            title=entry_title_with_whitespace, type="WORD", site=site
        )
        entry.save()
        fetched_entry = DictionaryEntry.objects.get(title=entry_title)
        assert fetched_entry.title == entry_title
        assert len(fetched_entry.custom_order) == 2 * title_length


class TestDictionarySortProcessing:
    @pytest.fixture
    def g2p_db_setup(self, django_db_blocker):
        with django_db_blocker.unblock():
            call_command("loaddata", "default_g2p_config.json")

    @pytest.mark.django_db
    def test_autocreate_alphabet_on_save(self, g2p_db_setup):
        """When no alphabet exists, creating sortable content should create it"""
        site = SiteFactory.create()
        assert len(Alphabet.objects.filter(site_id=site.id)) == 0
        ControlledSiteContentFactory.create(site=site)
        assert len(Alphabet.objects.filter(site_id=site.id)) == 1

    @pytest.mark.django_db
    def test_custom_sort_on_save(self, g2p_db_setup):
        """Saving sortable content should reapply sort"""
        alphabet = AlphabetFactory.create()
        content = ControlledSiteContentFactory.create(
            site=alphabet.site, title="qwerty", custom_order="x"
        )
        assert content.custom_order == alphabet.get_custom_order(content.title)

    @pytest.mark.django_db
    def test_clean_confusables_on_save(self, g2p_db_setup):
        """Saving sortable content should clean confusables"""
        alphabet = AlphabetFactory.create(
            input_to_canonical_map=[
                {"in": "old", "out": "new"},
            ],
        )
        title = "old-old"
        content = ControlledSiteContentFactory.create(site=alphabet.site, title=title)
        assert content.title != title
        assert content.title == alphabet.clean_confusables(title)
