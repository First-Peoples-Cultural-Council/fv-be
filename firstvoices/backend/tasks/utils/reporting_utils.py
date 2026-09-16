from celery.utils.log import get_task_logger
from import_export.results import RowResult

from backend.models.files import File
from backend.models.import_jobs import ImportJobReport, ImportJobReportRow
from backend.models.update_jobs import UpdateJobReport, UpdateJobReportRow
from backend.tasks.batch_utils import (
    create_or_append_error_row,
    get_failed_rows_csv_file,
    get_failed_rows_csv_file_for_update_job,
)


def generate_report(
    job,
    accepted_columns,
    ignored_columns,
    audio_import_results,
    document_import_results,
    img_import_results,
    video_import_results,
    dictionary_entry_import_result,
    report_model=ImportJobReport,
    report_row_model=ImportJobReportRow,
    report_job_relation_field="importjob",
    report_log_label="import_job",
):
    """
    Creates an ImportJobReport to summarize the results.
    Also Combines rows from media import and dictionary entries import.
    """
    logger = get_task_logger(__name__)

    # Clearing out old report if present
    old_report = job.validation_report

    if old_report:
        try:
            old_report = report_model.objects.filter(id=old_report.id)
            old_report.delete()
        except Exception as e:
            logger.error(
                f"Unable to delete previous report for {report_log_label}: {str(job.id)}. Error: {e}."
            )

    report = report_model(
        site=job.site,
        accepted_columns=accepted_columns,
        ignored_columns=ignored_columns,
        **{report_job_relation_field: job},
    )
    report.save()

    # Add errors from individual import results to report
    all_results = (
        [dictionary_entry_import_result]
        + audio_import_results
        + document_import_results
        + img_import_results
        + video_import_results
    )
    for result in all_results:
        for row in result.rows:
            # skipped rows without error messages were skipped intentionally
            if (
                row.import_type == RowResult.IMPORT_TYPE_SKIP
                and len(row.error_messages) > 0
            ):
                create_or_append_error_row(
                    job,
                    report,
                    row_number=row.number,
                    errors=row.error_messages,
                )

    report.new_rows = dictionary_entry_import_result.totals["new"]
    report.updated_rows = dictionary_entry_import_result.totals["update"]
    report.error_rows = report_row_model.objects.filter(report=report).count()
    report.save()

    return report


def generate_update_job_report(
    job,
    accepted_columns,
    ignored_columns,
    audio_import_results,
    document_import_results,
    img_import_results,
    video_import_results,
    dictionary_entry_import_result,
):
    return generate_report(
        job=job,
        accepted_columns=accepted_columns,
        ignored_columns=ignored_columns,
        audio_import_results=audio_import_results,
        document_import_results=document_import_results,
        img_import_results=img_import_results,
        video_import_results=video_import_results,
        dictionary_entry_import_result=dictionary_entry_import_result,
        report_model=UpdateJobReport,
        report_row_model=UpdateJobReportRow,
        report_job_relation_field="updatejob",
        report_log_label="update_job",
    )


def attach_csv_to_report(data, job, report, report_row_model=ImportJobReportRow):
    """
    Attaches an updated CSV file to the importJob if any errors occurred.
    """
    # Deleting old failed_rows_csv file if it exists
    if job.failed_rows_csv and job.failed_rows_csv.id:
        old_failed_rows_csv = File.objects.get(id=job.failed_rows_csv.id)
        old_failed_rows_csv.delete()
        job.failed_rows_csv = None

    # row numbers below 1 are job-level warnings/errors rather than real csv rows
    error_rows = list(
        report_row_model.objects.filter(report=report, row_number__gte=1).values_list(
            "row_number", flat=True
        )
    )
    error_rows.sort()

    if error_rows:
        failed_row_csv_file = get_failed_rows_csv_file(job, data, error_rows)
        job.failed_rows_csv = failed_row_csv_file

    job.save()


def attach_csv_to_update_job_report(
    data, job, report, report_row_model=UpdateJobReportRow
):
    """Attaches an updated CSV file to the updateJob if any row-level errors occurred."""
    # Deleting old failed_rows_csv file if it exists
    if job.failed_rows_csv and job.failed_rows_csv.id:
        old_failed_rows_csv = File.objects.get(id=job.failed_rows_csv.id)
        old_failed_rows_csv.delete()
        job.failed_rows_csv = None

    # row numbers below 1 are job-level warnings/errors rather than real csv rows
    error_rows = list(
        report_row_model.objects.filter(report=report, row_number__gte=1).values_list(
            "row_number", flat=True
        )
    )
    error_rows.sort()

    if error_rows:
        failed_row_csv_file = get_failed_rows_csv_file_for_update_job(
            job, data, error_rows
        )
        job.failed_rows_csv = failed_row_csv_file

    job.save()
