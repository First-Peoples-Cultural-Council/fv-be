import tablib
from celery import shared_task
from celery.utils.log import get_task_logger

from backend.models.import_jobs import (
    ImportJob,
    ImportJobReport,
    ImportJobReportRow,
    RowStatus,
)
from backend.resources.dictionary import DictionaryEntryResource


@shared_task
def execute_dry_run_import(import_job_instance_id, *args, **kwargs):
    # This function will be modified later with a flag
    # to be used for both dry-run and actual import

    logger = get_task_logger(__name__)

    import_job_instance = ImportJob.objects.get(id=import_job_instance_id)

    # Signals to be enabled during actual run, and not dry-run
    # After a batch has been successfully uploaded, we should run a
    # re-index for the site

    # Disconnecting search indexing signals
    # disconnect_signals()
    # logger.info("Disconnected all search index related signals")

    resource = DictionaryEntryResource(site=import_job_instance.site)

    table = tablib.Dataset().load(
        import_job_instance.data.content.open().read().decode("utf-8-sig"), format="csv"
    )
    table.headers = [header.lower() for header in table.headers]

    try:
        result = resource.import_data(dataset=table, dry_run=True)
    except Exception as e:
        logger.error(e)

    # Create an ImportJobReport for the run
    report = ImportJobReport(
        site=import_job_instance.site,
        importjob=import_job_instance,
        new_rows=result.totals["new"],
        skipped_rows=result.totals["skip"],
        error_rows=result.totals["error"],
    )
    report.save()

    import_job_instance.validation_report = report
    import_job_instance.save()

    # check for errors
    if result.has_errors():
        for row in result.error_rows:
            error_messages = []
            for e in row.errors:
                error_messages.append(str(e.error))
            error_row_instance = ImportJobReportRow(
                site=import_job_instance.site,
                report=report,
                status=RowStatus.ERROR,
                row_number=row.number,
                errors=error_messages,
            )
            error_row_instance.save()

    # Connecting back search indexing signals
    # connect_signals()
    # logger.info("Re-connected all search index related signals")
