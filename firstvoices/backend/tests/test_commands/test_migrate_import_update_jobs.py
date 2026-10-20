from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils.timezone import now

from backend.management.commands.migrate_import_update_jobs import Command
from backend.models.files import File, FileBase
from backend.models.import_jobs import (
    ImportJob,
    ImportJobMode,
    ImportJobReport,
    ImportJobReportRow,
    ImportJobStatus,
    RowStatus,
)
from backend.models.update_jobs import UpdateJob, UpdateJobReport, UpdateJobReportRow
from backend.tests import factories


@pytest.mark.django_db
class TestMigrateImportUpdateJobs:
    COMMAND = "migrate_import_update_jobs"

    @staticmethod
    def set_historical_dates(instance):
        historical_date = now().replace(month=1, day=1)
        type(instance).objects.filter(id=instance.id).update(
            created=historical_date.replace(year=2020),
            last_modified=historical_date.replace(year=2021, month=2, day=2),
            system_last_modified=historical_date.replace(year=2022, month=3, day=3),
        )

    @staticmethod
    def get_values(instance):
        return type(instance).objects.values().get(id=instance.id)

    @staticmethod
    def assert_migrated_values(actual, expected):
        actual = actual.copy()
        actual.pop("system_last_modified")
        expected = expected.copy()
        expected.pop("system_last_modified")
        assert actual == expected

    def test_preserves_jobs_reports_and_rows(self):
        site = factories.SiteFactory()
        report = factories.ImportJobReportFactory(
            site=site,
            new_rows=0,
            updated_rows=4,
            error_rows=1,
            warnings=2,
            accepted_columns=["id", "title"],
            ignored_columns=["unknown"],
        )
        rows = [
            factories.ImportJobReportRowFactory(
                site=site,
                report=report,
                status=RowStatus.ERROR,
                row_number=-1,
                errors=["WARNING: Values removed."],
            ),
            factories.ImportJobReportRowFactory(
                site=site,
                report=report,
                status=RowStatus.INVALID,
                row_number=2,
                errors=["Invalid value", "Missing media"],
            ),
        ]
        job = factories.ImportJobFactory(
            site=site,
            mode=ImportJobMode.UPDATE,
            validation_report=report,
            status=ImportJobStatus.COMPLETE,
            validation_status=ImportJobStatus.COMPLETE,
            task_id="historical-task",
            validation_task_id="historical-validation-task",
            message="Historical message",
            run_as_user=report.created_by,
        )
        ImportJob.objects.filter(id=job.id).update(failed_rows_csv_id=job.data_id)
        for instance in [job, report, *rows]:
            self.set_historical_dates(instance)

        expected_job = self.get_values(job)
        expected_job.pop("mode")
        expected_report = self.get_values(report)
        expected_rows = [self.get_values(row) for row in rows]

        call_command(self.COMMAND)

        self.assert_migrated_values(
            UpdateJob.objects.values().get(id=job.id), expected_job
        )
        self.assert_migrated_values(
            UpdateJobReport.objects.values().get(id=report.id),
            expected_report,
        )
        for expected_row in expected_rows:
            self.assert_migrated_values(
                UpdateJobReportRow.objects.values().get(id=expected_row["id"]),
                expected_row,
            )

        assert not ImportJob.objects.filter(id=job.id).exists()
        assert not ImportJobReport.objects.filter(id=report.id).exists()
        assert not ImportJobReportRow.objects.filter(report_id=report.id).exists()

    def test_preserves_files_entries_and_media(self):
        job = factories.ImportJobFactory(mode=ImportJobMode.UPDATE)
        audio = factories.AudioFactory(site=job.site)
        document = factories.DocumentFactory(site=job.site)
        image = factories.ImageFactory(site=job.site)
        video = factories.VideoFactory(site=job.site)
        media = [audio, document, image, video]
        entry = factories.DictionaryEntryFactory(site=job.site, import_job=job)

        # Attach each media type to the entry and its original file to the old job.
        entry.related_audio.add(audio)
        entry.related_documents.add(document)
        entry.related_images.add(image)
        entry.related_videos.add(video)
        for item in media:
            type(item.original).objects.filter(id=item.original_id).update(
                import_job=job
            )

        # Only the entry and original files should change their job ownership.
        ownership_records = [
            entry,
            audio.original,
            document.original,
            image.original,
            video.original,
        ]
        ownership_before = [
            (instance, self.get_values(instance)) for instance in ownership_records
        ]
        csv_before = self.get_values(job.data)
        media_before = [(item, self.get_values(item)) for item in media]
        storage = job.data.content.storage

        # Fail if migration invokes destructive cleanup or reads/writes stored files
        # This is to prevent any accidental deletions of import jobs or media files during the move.
        with (
            patch.object(
                ImportJob, "delete", side_effect=AssertionError("Instance delete")
            ),
            patch.object(FileBase, "save", side_effect=AssertionError("File save")),
            patch.object(FileBase, "delete", side_effect=AssertionError("File delete")),
            patch.object(
                storage, "delete", side_effect=AssertionError("Storage delete")
            ),
            patch.object(storage, "save", side_effect=AssertionError("Storage save")),
            patch.object(storage, "open", side_effect=AssertionError("Storage open")),
        ):
            call_command(self.COMMAND)

        for instance, expected in ownership_before:
            expected.update(import_job_id=None, update_job_id=job.id)
            assert self.get_values(instance) == expected

        # Verify that the CSV and media records, including their original-file links remain unchanged after migration.

        # CSV
        assert self.get_values(job.data) == csv_before

        # Media
        for item, expected in media_before:
            assert self.get_values(item) == expected
        assert list(entry.related_audio.all()) == [audio]
        assert list(entry.related_documents.all()) == [document]
        assert list(entry.related_images.all()) == [image]
        assert list(entry.related_videos.all()) == [video]

    @pytest.mark.parametrize("with_report", [False, True])
    def test_optional_associations_and_rerun(self, with_report, caplog):
        report = factories.ImportJobReportFactory() if with_report else None
        job = factories.ImportJobFactory(
            mode=ImportJobMode.UPDATE,
            data=None,
            validation_report=report,
            status=None,
            validation_status=None,
        )
        expected = self.get_values(job)
        expected.pop("mode")

        call_command(self.COMMAND)
        migrated = UpdateJob.objects.values().get(id=job.id)
        call_command(self.COMMAND)

        assert UpdateJob.objects.values().get(id=job.id) == migrated
        self.assert_migrated_values(migrated, expected)

        assert UpdateJob.objects.count() == 1
        assert UpdateJobReport.objects.count() == int(with_report)
        assert UpdateJobReportRow.objects.count() == 0
        assert "No historical update-mode import jobs found." in caplog.text

    def test_dry_run_lists_all_jobs_without_changes(self, caplog):
        jobs = [
            factories.ImportJobFactory(mode=ImportJobMode.UPDATE),
            factories.ImportJobFactory(mode=ImportJobMode.UPDATE),
        ]
        report = factories.ImportJobReportFactory(site=jobs[0].site)
        row = factories.ImportJobReportRowFactory(report=report, site=jobs[0].site)

        ImportJob.objects.filter(id=jobs[0].id).update(validation_report=report)
        entry = factories.DictionaryEntryFactory(site=jobs[0].site, import_job=jobs[0])
        audio = factories.AudioFactory(site=jobs[0].site)
        document = factories.DocumentFactory(site=jobs[0].site)
        for item in (audio, document):
            type(item.original).objects.filter(id=item.original_id).update(
                import_job=jobs[0]
            )

        instances = [
            *jobs,
            report,
            row,
            entry,
            audio,
            document,
            audio.original,
            document.original,
            *(job.data for job in jobs),
        ]
        expected = [self.get_values(instance) for instance in instances]

        call_command(self.COMMAND, dry_run=True)

        assert [self.get_values(instance) for instance in instances] == expected
        assert not UpdateJob.objects.exists()
        assert not UpdateJobReport.objects.exists()
        assert not UpdateJobReportRow.objects.exists()

        for job in jobs:
            assert str(job.id) in caplog.text
            assert job.site.slug in caplog.text
            assert str(job.data_id) in caplog.text
        assert "'jobs': 2" in caplog.text
        assert "'report_rows': 1" in caplog.text
        assert "'entries': 1" in caplog.text
        assert "'files': 2" in caplog.text
        assert "'audio': 1" in caplog.text
        assert "'documents': 1" in caplog.text
        assert "'reports': 1" in caplog.text

        job_log_records = [
            record.getMessage()
            for record in caplog.records
            if record.getMessage().startswith("Would migrate job")
        ]
        assert len(job_log_records) == 2
        assert all("'reports':" not in message for message in job_log_records)
        assert "No changes made" in caplog.text

    def test_failure_on_later_job_rolls_back_everything(self, monkeypatch):
        original_records = []

        # Create two jobs with reports, entries, and owned CSV files to restore.
        for _ in range(2):
            report = factories.ImportJobReportFactory()
            row = factories.ImportJobReportRowFactory(report=report, site=report.site)
            job = factories.ImportJobFactory(
                mode=ImportJobMode.UPDATE, site=report.site, validation_report=report
            )
            entry = factories.DictionaryEntryFactory(site=job.site, import_job=job)
            File.objects.filter(id=job.data_id).update(import_job=job)
            for instance in (job, report, row, entry, job.data):
                original_records.append((instance, self.get_values(instance)))

        original_migrate_job = Command.migrate_job
        completed_jobs = []

        # Run the real migration for both jobs, then fail after source cleanup.
        def fail_after_second_job(command, job):
            original_migrate_job(command, job)
            completed_jobs.append(job.id)
            if len(completed_jobs) == 2:
                raise RuntimeError("Simulated failure after source cleanup")

        monkeypatch.setattr(Command, "migrate_job", fail_after_second_job)
        with pytest.raises(RuntimeError, match="Simulated failure"):
            call_command(self.COMMAND)

        # Both completed migrations must be undone, including file/entry ownership.
        assert len(completed_jobs) == 2
        for instance, expected in original_records:
            assert self.get_values(instance) == expected
        assert not UpdateJob.objects.exists()
        assert not UpdateJobReport.objects.exists()
        assert not UpdateJobReportRow.objects.exists()
