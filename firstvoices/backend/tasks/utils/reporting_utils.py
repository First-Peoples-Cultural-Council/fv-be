from celery.utils.log import get_task_logger
from import_export.results import RowResult

from backend.models.files import File
from backend.models.import_jobs import ImportJobReport, ImportJobReportRow
from backend.tasks.batch_utils import (
    create_or_append_error_row,
    get_failed_rows_csv_file,
)


def generate_report(
    import_job,
    accepted_columns,
    ignored_columns,
    audio_import_results,
    document_import_results,
    img_import_results,
    video_import_results,
    dictionary_entry_import_result,
):
    """
    Creates an ImportJobReport to summarize the results.
    Also combines rows from missing_media, audio import and dictionary entries import.
    """
    logger = get_task_logger(__name__)

    # Clearing out old report if present
    old_report = import_job.validation_report

    if old_report:
        try:
            old_report = ImportJobReport.objects.filter(id=old_report.id)
            old_report.delete()
        except Exception as e:
            logger.error(
                f"Unable to delete previous report for import_job: {str(import_job.id)}. Error: {e}."
            )

    report = ImportJobReport(
        site=import_job.site,
        importjob=import_job,
        accepted_columns=accepted_columns,
        ignored_columns=ignored_columns,
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
                    import_job,
                    report,
                    row_number=row.number,
                    errors=row.error_messages,
                )

    report.new_rows = dictionary_entry_import_result.totals["new"]
    report.updated_rows = dictionary_entry_import_result.totals["update"]
    report.error_rows = ImportJobReportRow.objects.filter(report=report).count()
    report.save()

    return report


def attach_csv_to_report(data, import_job, report):
    """
    Attaches an updated CSV file to the importJob if any errors occurred.
    """
    # Deleting old failed_rows_csv file if it exists
    if import_job.failed_rows_csv and import_job.failed_rows_csv.id:
        old_failed_rows_csv = File.objects.get(id=import_job.failed_rows_csv.id)
        old_failed_rows_csv.delete()
        import_job.failed_rows_csv = None

    if report.error_rows:
        error_rows = list(
            ImportJobReportRow.objects.filter(report=report).values_list(
                "row_number", flat=True
            )
        )
        error_rows.sort()
        failed_row_csv_file = get_failed_rows_csv_file(import_job, data, error_rows)
        import_job.failed_rows_csv = failed_row_csv_file

    import_job.save()
