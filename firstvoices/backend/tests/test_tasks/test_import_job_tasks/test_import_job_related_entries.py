import pytest

from backend.models import DictionaryEntry
from backend.models.constants import Visibility
from backend.models.import_jobs import JobStatus
from backend.tasks.import_job_tasks import confirm_import_job
from backend.tests import factories
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestImportJobRelatedEntries:
    MIMETYPE = "text/csv"
    CSV_FILES_DIR = "test_tasks/test_import_job_tasks/resources"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def test_multiple_related_entries_by_id(self):
        # For entries that are already present in the db
        existing_entry1 = factories.DictionaryEntryFactory.create(
            site=self.site, id="964b2b52-45c3-4c2f-90db-7f34c6599c1c"
        )
        existing_entry2 = factories.DictionaryEntryFactory.create(
            site=self.site, id="f93eb512-c0bc-49ac-bbf7-86ac1a9dc89d"
        )

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_entries_by_id.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 3

        new_entry = DictionaryEntry.objects.get(
            title="test_related_entries_by_id_word_1"
        )
        related_entry_list = [
            str(value)
            for value in new_entry.dictionaryentrylink_set.values_list(
                "to_dictionary_entry_id", flat=True
            )
        ]

        assert len(related_entry_list) == 2
        assert existing_entry1.id in related_entry_list
        assert existing_entry2.id in related_entry_list

    def test_related_entries_by_title(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_entries_by_title.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 2

        entry1 = DictionaryEntry.objects.get(
            title="test_related_entries_by_title_word_1"
        )
        related_entry1 = entry1.dictionaryentrylink_set.first()
        assert (
            related_entry1.to_dictionary_entry.title
            == "test_related_entries_by_title_word_2"
        )

        entry2 = DictionaryEntry.objects.get(
            title="test_related_entries_by_title_word_2"
        )
        related_entry2 = entry2.dictionaryentrylink_set.first()
        assert (
            related_entry2.to_dictionary_entry.title
            == "test_related_entries_by_title_word_1"
        )

    def test_related_entries_by_title_multiple(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_entries_by_title_multiple.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 6

        entry1 = DictionaryEntry.objects.get(
            title="test_related_entries_by_title_multiple_word_1"
        )
        related_entries = entry1.dictionaryentrylink_set.all()
        assert related_entries.count() == 5

        expected_related_titles = [
            "test_related_entries_by_title_multiple_word_2",
            "test_related_entries_by_title_multiple_word_3",
            "test_related_entries_by_title_multiple_phrase_1",
            "test_related_entries_by_title_multiple_phrase_2",
            "test_related_entries_by_title_multiple_phrase_3",
        ]
        actual_related_titles = [
            related_entry.to_dictionary_entry.title for related_entry in related_entries
        ]
        assert all(title in actual_related_titles for title in expected_related_titles)

    def test_related_entries_duplicate_titles(self):
        # If there are multiple entries with the same title, only link the first instance of that title
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_entries_duplicate_titles.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 3

        entry1 = DictionaryEntry.objects.get(
            title="test_related_entries_duplicate_titles_word_1"
        )
        related_entries = entry1.dictionaryentrylink_set.all()
        assert related_entries.count() == 1
        assert (
            related_entries[0].to_dictionary_entry.title
            == "test_related_entries_duplicate_titles_word_2"
        )
        assert related_entries[0].to_dictionary_entry.notes[0] == "first instance"

    def test_related_entries_duplicate_titles_same_row(self):
        # Ensure no duplicate links are created if the same title is in the same row multiple times
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_entries_duplicate_titles_same_row.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 1

    def test_related_entries_cannot_link_to_self(self):
        # Ensure no links are created to self
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_entries_cannot_link_to_self.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 1

        entry1 = DictionaryEntry.objects.get(
            title="test_related_entries_cannot_link_to_self_word_1"
        )
        related_entries = entry1.dictionaryentrylink_set.all()
        assert related_entries.count() == 0

    def test_skip_rows_with_erroneous_values(self):
        # If a row has validation errors, skip that row, but import the rest of the file
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_skip_rows_with_erroneous_values.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
        )
        confirm_import_job(import_job.id)

        imported_entries = DictionaryEntry.objects.filter(site=self.site)
        assert len(imported_entries) == 1
        assert (
            imported_entries[0].title == "test_skip_rows_with_erroneous_values_phrase_1"
        )

    def test_invalid_m2m_entries_not_imported(self):
        # Testing out with categories, but is similar
        # for any m2m relation.

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_invalid_m2m_entries_not_imported.csv",
            mimetype=self.MIMETYPE,
        )  # 1st row in the file a valid row for control
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.filter(
            title="test_invalid_m2m_entries_not_imported_valid_entry"
        ).exists()

        assert not DictionaryEntry.objects.filter(
            title="test_invalid_m2m_entries_not_imported_invalid_category"
        ).exists()

    def test_related_entry_import_missing_to_entry(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_entry_import_missing_to_entry.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            data=file,
            run_as_user=self.user,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.count() == 0
