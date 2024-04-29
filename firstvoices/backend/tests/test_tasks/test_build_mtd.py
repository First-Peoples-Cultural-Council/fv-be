import logging

import pytest

from backend.models import MTDExportFormat
from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tasks.build_mtd_export_format import build_index_and_calculate_scores
from backend.tests import factories

LOGGER = logging.getLogger(__name__)


class TestMTDIndexAndScoreTask:
    sample_entry_title = "title_one word"

    @pytest.fixture
    def site(self):
        return factories.SiteFactory.create(slug="test")

    @pytest.mark.django_db
    def test_build_empty(self, site):
        result = build_index_and_calculate_scores(site.slug)
        assert result["config"]["L1"] == site.title
        assert len(result["data"]) == 0
        assert len(result["l1_index"]) == 0
        assert len(result["l2_index"]) == 0

    @pytest.mark.django_db
    def test_validation_error(self, site, caplog):
        """If a validation error happens with a DictionaryEntry
           The entry should be skipped, but logged as a warning.

        Args:
            site (Union[str, Site])): site or site slug
        """
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title=self.sample_entry_title,
        )
        build_index_and_calculate_scores(site.slug)
        # Logs entry id
        assert str(entry_one.id) in caplog.text
        # Logs the type of error, in this case, Definition (str, required) is None
        assert "type=string_type, input_value=None" in caplog.text

    @pytest.mark.django_db
    def test_only_include_public_entries(self, site):
        """Only public entries should be included in MTD exports.

        Args:
            site (Union[str, Site])): site or site slug
        """
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.TEAM,
            type=TypeOfDictionaryEntry.WORD,
            title=self.sample_entry_title,
        )
        entry_one_translations = [factories.TranslationFactory.create()]
        entry_one.translation_set.set(entry_one_translations)
        entry_two = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title=self.sample_entry_title,
        )
        entry_two_translations = [factories.TranslationFactory.create()]
        entry_two.translation_set.set(entry_two_translations)
        result = build_index_and_calculate_scores(site.slug)
        assert len(result["data"]) == 1

    @pytest.mark.django_db
    def test_export_is_saved(self, site):
        result = build_index_and_calculate_scores(site.slug)
        # Check that the exported contents were saved
        saved_export_format = MTDExportFormat.objects.filter(site=site)
        assert saved_export_format.latest().latest_export_result == result
        assert not saved_export_format.latest().is_preview

    @pytest.mark.django_db
    def test_build_and_score(self, site):
        # Add some entries
        speaker = factories.PersonFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        factories.AudioSpeakerFactory.create(audio=audio, speaker=speaker)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)
        parent_category = factories.CategoryFactory.create(site=site)
        child_category = factories.CategoryFactory.create(
            site=site, parent=parent_category
        )
        entry_one_translations = [factories.TranslationFactory.create()]
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title=self.sample_entry_title,
            related_audio=[audio],
            related_images=[image],
            related_videos=[video],
        )
        factories.DictionaryEntryCategoryFactory.create(
            category=parent_category, dictionary_entry=entry_one
        )
        factories.DictionaryEntryCategoryFactory.create(
            category=child_category, dictionary_entry=entry_one
        )

        entry_one.translation_set.set(entry_one_translations)
        entry_two_translations = [factories.TranslationFactory.create()]
        entry_two = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.PHRASE,
            title="title_two",
        )
        entry_two.translation_set.set(entry_two_translations)
        entry_three_translations = [factories.TranslationFactory.create()]
        entry_three = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.PHRASE,
            title="the word 'third' appears as the third word in this sentence",
        )
        entry_three.translation_set.set(entry_three_translations)
        # Build and index
        result = build_index_and_calculate_scores(site.slug)
        assert len(result["data"]) == 3
        assert result["data"][1]["word"] == self.sample_entry_title
        # punctuation is removed by default so it is titleone in the index
        assert result["data"][1]["entryID"] in result["l1_index"]["titleone"]
        # assert location of 'third' as the third word
        assert result["l1_index"]["third"][str(entry_three.id)]["location"][0] == [
            "word",
            2,
        ]
        # it also exists as the 7th word
        assert result["l1_index"]["third"][str(entry_three.id)]["location"][1] == [
            "word",
            6,
        ]
        # the word 'word' occurs in two entries
        assert len(result["l1_index"]["word"].keys()) == 2
        # result for entry_one word should be higher with default search settings because
        # it has fewer overall words
        assert (
            result["l1_index"]["word"][str(entry_one.id)]["score"]["total"]
            > result["l1_index"]["word"][str(entry_three.id)]["score"]["total"]
        )

        assert len(result["data"][1]["audio"]) == 1
        assert result["data"][1]["img"] is not None
        assert len(result["data"][1]["video"]) == 1

    @pytest.mark.django_db
    def test_old_results_removed(self, site):
        build_index_and_calculate_scores(site.slug)
        build_index_and_calculate_scores(site.slug)
        final_result = build_index_and_calculate_scores(site.slug)

        # Check that only the most recent is in the db
        saved_results = MTDExportFormat.objects.filter(site=site)
        assert len(saved_results) == 1
        assert saved_results.latest().latest_export_result == final_result
        assert not saved_results.latest().is_preview
