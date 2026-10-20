import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from backend.models.dictionary import DictionaryEntry
from backend.models.files import File
from backend.models.import_jobs import ImportJob, ImportJobMode, ImportJobReport
from backend.models.media import Audio, Document, ImageFile, VideoFile
from backend.models.update_jobs import UpdateJob, UpdateJobReport, UpdateJobReportRow

# Ensure no relevant celery tasks are pending or active. Review --dry-run first.
# After migration, rebuild only the dictionary index:
# python manage.py rebuild_index --index dictionary_entries


class Command(BaseCommand):
    help = "Move historical update-mode import jobs into update jobs, preserving reports and files. "

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="List affected jobs and associated counts without making changes.",
        )

    @staticmethod
    def get_base_fields(instance):
        return {
            "id": instance.id,
            "site_id": instance.site_id,
            "created": instance.created,
            "created_by_id": instance.created_by_id,
            "last_modified": instance.last_modified,
            "last_modified_by_id": instance.last_modified_by_id,
            "system_last_modified_by_id": instance.system_last_modified_by_id,
        }

    def copy_report(self, report):
        UpdateJobReport.objects.create(
            **self.get_base_fields(report),
            new_rows=report.new_rows,
            error_rows=report.error_rows,
            updated_rows=report.updated_rows,
            warnings=report.warnings,
            accepted_columns=report.accepted_columns,
            ignored_columns=report.ignored_columns,
        )
        for row in report.rows.all():
            UpdateJobReportRow.objects.create(
                **self.get_base_fields(row),
                report_id=report.id,
                status=row.status,
                errors=row.errors,
                row_number=row.row_number,
                identifier_field=row.identifier_field,
                identifier_value=row.identifier_value,
            )

    def migrate_job(self, job):
        if job.validation_report_id:
            self.copy_report(job.validation_report)

        UpdateJob.objects.create(
            **self.get_base_fields(job),
            title=job.title,
            run_as_user_id=job.run_as_user_id,
            data_id=job.data_id,
            status=job.status,
            task_id=job.task_id,
            message=job.message,
            validation_task_id=job.validation_task_id,
            validation_status=job.validation_status,
            validation_report_id=job.validation_report_id,
            failed_rows_csv_id=job.failed_rows_csv_id,
        )

        # Copying related CSVs, and associated media to the new update job.
        for model in (DictionaryEntry, File, ImageFile, VideoFile):
            model.objects.filter(import_job_id=job.id).update(
                update_job_id=job.id, import_job_id=None
            )

        # Instance deletion would also delete the old associated CSVs and uploaded files.
        ImportJob.objects.filter(pk=job.id).delete()
        if job.validation_report_id:
            ImportJobReport.objects.filter(pk=job.validation_report_id).delete()

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        jobs = list(
            ImportJob.objects.filter(mode=ImportJobMode.UPDATE).order_by(
                "created", "id"
            )
        )
        if not jobs:
            self.logger.info("No historical update-mode import jobs found.")
            return

        totals = {
            "jobs": len(jobs),
            "reports": 0,
            "report_rows": 0,
            "entries": 0,
            "files": 0,
            "audio": 0,
            "documents": 0,
            "images": 0,
            "videos": 0,
        }
        with transaction.atomic():
            for job in jobs:
                counts = {
                    "report_rows": (
                        job.validation_report.rows.count()
                        if job.validation_report_id
                        else 0
                    ),
                    "entries": DictionaryEntry.objects.filter(
                        import_job_id=job.id
                    ).count(),
                    "files": File.objects.filter(import_job_id=job.id).count(),
                    "audio": Audio.objects.filter(
                        original__import_job_id=job.id
                    ).count(),
                    "documents": Document.objects.filter(
                        original__import_job_id=job.id
                    ).count(),
                    "images": ImageFile.objects.filter(import_job_id=job.id).count(),
                    "videos": VideoFile.objects.filter(import_job_id=job.id).count(),
                }
                self.logger.info(
                    "%s job %s, title=%r, site=%s, status=%s, validation_status=%s, "
                    "report=%s, data=%s, failed_rows_csv=%s, counts=%s",
                    "Would migrate" if dry_run else "Migrating",
                    job.id,
                    job.title,
                    job.site.slug,
                    job.status,
                    job.validation_status,
                    job.validation_report_id,
                    job.data_id,
                    job.failed_rows_csv_id,
                    counts,
                )
                for name, count in counts.items():
                    totals[name] += count
                totals["reports"] += int(job.validation_report_id is not None)

                if not dry_run:
                    self.migrate_job(job)

        if dry_run:
            self.logger.info("Dry run complete. No changes made. Totals: %s", totals)
        else:
            self.logger.info(
                "Historical update jobs migrated successfully. Totals: %s", totals
            )
