import pytest

from backend.models import MTDExportFormat
from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tasks.build_mtd_export_format import build_index_and_calculate_scores
from backend.tests import factories


class TestMTDIndexAndScoreTask:
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
    def test_export_is_saved(self, site):
        result = build_index_and_calculate_scores(site.slug)
        # Check that the exported contents were saved
        saved_export_format = MTDExportFormat.objects.filter(site=site)
        assert result == saved_export_format.latest().latest_export_result
        assert result["config"]["L1"] == site.title
        assert len(result["data"]) == 0
        assert len(result["l1_index"]) == 0
        assert len(result["l2_index"]) == 0

    @pytest.mark.django_db
    def test_build_and_score(self, site):
        # Add some entries
        speaker = factories.PersonFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        factories.AudioSpeakerFactory.create(audio=audio, speaker=speaker)
        image = factories.ImageFactory.create(site=site)
        parent_category = factories.CategoryFactory.create(site=site)
        child_category = factories.CategoryFactory.create(
            site=site, parent=parent_category
        )
        entry_one_translations = [factories.TranslationFactory.create()]
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title="title_one word",
            related_audio=[audio],
            related_images=[image],
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
        assert result["data"][1]["word"] == "title_one word"
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
        # result for title_one word should be higher with default search settings because
        # it has fewer overall words
        assert (
            result["l1_index"]["word"][str(entry_one.id)]["score"]["total"]
            > result["l1_index"]["word"][str(entry_three.id)]["score"]["total"]
        )
