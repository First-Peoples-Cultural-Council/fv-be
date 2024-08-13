from datetime import timedelta

import pytest
from django.utils import timezone

from backend.models import MTDExportFormat
from backend.models.constants import Visibility
from backend.models.dictionary import DictionaryEntry, TypeOfDictionaryEntry
from backend.models.media import Audio
from backend.tasks.mtd_export_tasks import (
    build_index_and_calculate_scores,
    check_sites_for_mtd_sync,
)
from backend.tasks.utils import ASYNC_TASK_END_TEMPLATE
from backend.tests import factories
from firstvoices.celery import link_error_handler


class TestMTDIndexAndScoreTask:
    sample_entry_title = "title_one word"

    @staticmethod
    def assert_async_task_logs(site, caplog):
        assert f"Task started. Additional info: site: {site.slug}." in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text

    @pytest.fixture
    def site(self):
        return factories.SiteFactory.create(slug="test")

    @pytest.mark.django_db
    def test_build_empty(self, site, caplog):
        result = build_index_and_calculate_scores(site.slug)
        assert result["config"]["L1"] == site.title
        assert len(result["data"]) == 0
        assert len(result["l1_index"]) == 0
        assert len(result["l2_index"]) == 0

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_missing_translation(self, site, caplog):
        """The entry should be skipped.

        Args:
            site (Union[str, Site])): site or site slug
        """
        factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title=self.sample_entry_title,
            translations=[],
        )
        result = build_index_and_calculate_scores(site.slug)

        assert result["config"]["L1"] == site.title
        assert len(result["data"]) == 0
        assert len(result["l1_index"]) == 0
        assert len(result["l2_index"]) == 0

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_only_include_public_entries(self, site):
        """Only public entries should be included in MTD exports.

        Args:
            site (Union[str, Site])): site or site slug
        """
        factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.TEAM,
            type=TypeOfDictionaryEntry.WORD,
            title=self.sample_entry_title,
        )
        factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title=self.sample_entry_title,
        )
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
    @pytest.mark.disable_thumbnail_mocks
    def test_build_and_score(self, site, caplog):
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

        # entry_two
        factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.PHRASE,
            title="title_two",
        )
        entry_three = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.PHRASE,
            title="the word 'third' appears as the third word in this sentence",
        )
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

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    @pytest.mark.disable_thumbnail_mocks
    def test_build_and_score_bad_image_data(self, site, caplog):
        # build an entry with a bad image
        speaker = factories.PersonFactory.create(site=site)
        audio = factories.AudioFactory.create(site=site)
        factories.AudioSpeakerFactory.create(audio=audio, speaker=speaker)

        bad_image = factories.ImageFactory.create(site=site)
        bad_image.small = None
        bad_image.save()

        video = factories.VideoFactory.create(site=site)
        parent_category = factories.CategoryFactory.create(site=site)
        child_category = factories.CategoryFactory.create(
            site=site, parent=parent_category
        )
        entry_one = factories.DictionaryEntryFactory.create(
            site=site,
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            title=self.sample_entry_title,
            related_audio=[audio],
            related_images=[bad_image],
            related_videos=[video],
        )
        factories.DictionaryEntryCategoryFactory.create(
            category=parent_category, dictionary_entry=entry_one
        )
        factories.DictionaryEntryCategoryFactory.create(
            category=child_category, dictionary_entry=entry_one
        )

        # Build and index
        result = build_index_and_calculate_scores(site.slug)
        assert len(result["data"]) == 1
        assert result["data"][0]["word"] == self.sample_entry_title
        assert result["data"][0]["img"] is None
        assert len(result["data"][0]["audio"]) == 1
        assert len(result["data"][0]["video"]) == 1

        self.assert_async_task_logs(site, caplog)

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


class TestCheckSitesForMTDSyncTask:
    @pytest.fixture(scope="function", autouse=True)
    def mocked_mtd_build_func(self, mocker):
        self.mocked_func = mocker.patch(
            "backend.tasks.mtd_export_tasks.build_index_and_calculate_scores.apply_async"
        )

    @pytest.fixture
    def sites(self):
        return {
            "site_one": factories.SiteFactory.create(
                slug="site_one", visibility=Visibility.PUBLIC
            ),
            "site_two": factories.SiteFactory.create(
                slug="site_two", visibility=Visibility.PUBLIC
            ),
            "site_three": factories.SiteFactory.create(
                slug="site_three", visibility=Visibility.PUBLIC
            ),
        }

    @pytest.mark.django_db
    def test_no_sites_eligible_to_sync(self):
        result = check_sites_for_mtd_sync.apply()
        assert result.state == "SUCCESS"
        assert self.mocked_func.call_count == 0

    @pytest.mark.django_db
    @pytest.mark.parametrize("visibility", [Visibility.MEMBERS, Visibility.TEAM])
    def test_no_sites_eligible_to_sync_private(self, sites, visibility):
        private_site = factories.SiteFactory.create(visibility=visibility)
        factories.DictionaryEntryFactory.create(site=private_site)

        result = check_sites_for_mtd_sync.apply()
        assert result.state == "SUCCESS"
        assert self.mocked_func.call_count == 0

    @pytest.mark.django_db
    def test_single_site_updated_entries(self, sites):
        factories.DictionaryEntryFactory.create(site=sites["site_one"])
        result = check_sites_for_mtd_sync.apply()
        assert result.state == "SUCCESS"
        assert self.mocked_func.call_count == 1
        self.mocked_func.assert_called_once_with(
            (sites["site_one"].slug,), link_error=link_error_handler.s()
        )

    @pytest.mark.django_db
    def test_single_site_updated_categories(self, sites):
        seven_hours_ago = timezone.now() - timedelta(hours=7)
        category = factories.CategoryFactory.create(site=sites["site_one"])
        entry = factories.DictionaryEntryFactory.create(site=sites["site_one"])

        # update the timestamps to not trigger the updated entries check
        DictionaryEntry.objects.filter(id=entry.id).update(
            created=seven_hours_ago, last_modified=seven_hours_ago
        )

        check_sites_for_mtd_sync.apply()
        assert self.mocked_func.call_count == 0

        entry.categories.add(category)
        entry.save()

        result = check_sites_for_mtd_sync.apply()
        assert result.state == "SUCCESS"
        assert self.mocked_func.call_count == 1
        self.mocked_func.assert_called_once_with(
            (sites["site_one"].slug,), link_error=link_error_handler.s()
        )

    @pytest.mark.django_db
    def test_single_site_updated_related_media(self, sites):
        seven_hours_ago = timezone.now() - timedelta(hours=7)
        audio = factories.AudioFactory.create(site=sites["site_one"])
        entry = factories.DictionaryEntryFactory.create(site=sites["site_one"])

        # update the timestamps to not trigger the updated entries check
        DictionaryEntry.objects.filter(id=entry.id).update(
            created=seven_hours_ago, last_modified=seven_hours_ago
        )

        check_sites_for_mtd_sync.apply()
        assert self.mocked_func.call_count == 0

        entry.related_audio.add(audio)
        entry.save()

        result = check_sites_for_mtd_sync.apply()
        assert result.state == "SUCCESS"
        assert self.mocked_func.call_count == 1
        self.mocked_func.assert_called_once_with(
            (sites["site_one"].slug,), link_error=link_error_handler.s()
        )

    @pytest.mark.django_db
    def test_single_site_remove_related_media(self, sites):
        seven_hours_ago = timezone.now() - timedelta(hours=7)
        audio = factories.AudioFactory.create(site=sites["site_one"])
        entry = factories.DictionaryEntryFactory.create(site=sites["site_one"])
        entry.related_audio.add(audio)

        # update the timestamps to not trigger the updated entries check
        DictionaryEntry.objects.filter(id=entry.id).update(
            created=seven_hours_ago, last_modified=seven_hours_ago
        )
        Audio.objects.filter(id=audio.id).update(
            created=seven_hours_ago, last_modified=seven_hours_ago
        )

        check_sites_for_mtd_sync.apply()
        assert self.mocked_func.call_count == 0

        entry.related_audio.remove(audio)
        entry.save()

        result = check_sites_for_mtd_sync.apply()
        assert result.state == "SUCCESS"
        assert self.mocked_func.call_count == 1
        self.mocked_func.assert_called_once_with(
            (sites["site_one"].slug,), link_error=link_error_handler.s()
        )

    @pytest.mark.django_db
    def test_single_site_all_updates(self, sites):
        audio = factories.AudioFactory.create(site=sites["site_one"])
        category = factories.CategoryFactory.create(site=sites["site_one"])
        entry = factories.DictionaryEntryFactory.create(site=sites["site_one"])

        entry.related_audio.add(audio)
        entry.categories.add(category)
        entry.save()

        result = check_sites_for_mtd_sync.apply()
        assert result.state == "SUCCESS"
        assert self.mocked_func.call_count == 1
        self.mocked_func.assert_called_once_with(
            (sites["site_one"].slug,), link_error=link_error_handler.s()
        )

    @pytest.mark.django_db
    def test_multiple_sites_updated_entries(self, sites):
        factories.DictionaryEntryFactory.create(site=sites["site_one"])
        factories.DictionaryEntryFactory.create(site=sites["site_two"])
        factories.DictionaryEntryFactory.create(site=sites["site_three"])
        result = check_sites_for_mtd_sync.apply()
        assert result.state == "SUCCESS"
        assert self.mocked_func.call_count == 3

    @pytest.mark.django_db
    def test_check_for_sync_error(self, sites):
        factories.DictionaryEntryFactory.create(site=sites["site_one"])
        self.mocked_func.side_effect = Exception("Error")
        result = check_sites_for_mtd_sync.apply()
        assert result.state == "FAILURE"
