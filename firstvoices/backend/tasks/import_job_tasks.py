from copy import deepcopy

import tablib
from celery import current_task, shared_task
from celery.utils.log import get_task_logger
from import_export.results import RowResult
from rest_framework.exceptions import ValidationError

from backend.models.import_jobs import (
    ImportJob,
    ImportJobReport,
    ImportJobReportRow,
    JobStatus,
    RowStatus,
)
from backend.resources.dictionary import DictionaryEntryResource
from backend.tasks.utils import (
    ASYNC_TASK_END_TEMPLATE,
    ASYNC_TASK_START_TEMPLATE,
    get_failed_rows_csv_file,
    verify_no_other_import_jobs_running,
)

VALID_HEADERS = [
    "title",
    "type",
    "translation",
    "audio",
    "image",
    "video",
    "video_embed_link",
    "category",
    "note",
    "acknowledgement",
    "part_of_speech",
    "pronunciation",
    "alternate_spelling",
    "visibility",
    "include_on_kids_site",
    "include_in_games",
    "related_entry",
]


def is_valid_header_variation(input_header, all_headers):
    # The input header can have a _n variation from 2 to 5, e.g. 'note_5'
    # The original header also has to be present for the variation to be accepted,
    # e.g. 'note_2' to 'note_5' columns will only be accepted if 'note' column is present in the table
    # All other variations are invalid

    all_headers = [h.strip().lower() for h in all_headers]

    splits = input_header.split("_")
    if len(splits) >= 2:
        prefix = "_".join(splits[:-1])
        variation = splits[-1]
    else:
        prefix = input_header
        variation = None

    # Check if the prefix is a valid header
    if (
        prefix in VALID_HEADERS
        and prefix in all_headers
        and variation
        and variation.isdigit()
    ):
        variation = int(variation)
        if variation <= 1 or variation > 5:
            # Variation out of range. Skipping column.
            return False
    else:
        return False

    return True


def clean_csv(data):
    """
    Method to run validations on a csv file and returns a list of
    accepted columns, ignored columns and a cleaned csv for importing.
    This method also drops the ignored columns as those will not be used during import.
    """

    cleaned_data = deepcopy(data)  # so we keep an original copy for return purposes
    all_headers = data.headers
    accepted_headers = []
    invalid_headers = []

    # If any invalid headers are present, skip them and raise a warning
    for header in all_headers:
        cleaned_header = header.strip().lower()
        if cleaned_header in VALID_HEADERS:
            accepted_headers.append(header)
        elif is_valid_header_variation(cleaned_header, all_headers):
            accepted_headers.append(header)
        else:
            invalid_headers.append(header)

    # Dropping invalid columns
    for invalid_header in invalid_headers:
        del cleaned_data[invalid_header]

    # lower-casing headers
    cleaned_data.headers = [header.lower() for header in cleaned_data.headers]

    return accepted_headers, invalid_headers, cleaned_data


def import_resource(
    data,
    resource,
    import_job_instance,
    dry_run,
):
    accepted_columns, ignored_columns, cleaned_data = clean_csv(data)

    # Method to import the cleaned data for the provided resource along with a dry-run flag.
    result = resource.import_data(dataset=cleaned_data, dry_run=dry_run)

    # Create an ImportJobReport for the run
    report = ImportJobReport(
        site=import_job_instance.site,
        importjob=import_job_instance,
        new_rows=result.totals["new"],
        error_rows=result.totals["error"]
        + result.totals["invalid"]
        + result.totals["skip"],
        accepted_columns=accepted_columns,
        ignored_columns=ignored_columns,
    )
    report.save()

    # to keep track of row numbers of erroneous rows
    error_row_numbers = []

    # Adding error messages to the report
    for row in result.rows:
        if row.import_type == RowResult.IMPORT_TYPE_SKIP:
            error_row_instance = ImportJobReportRow(
                site=import_job_instance.site,
                report=report,
                status=RowStatus.ERROR,
                row_number=row.number,
                errors=row.error_messages,
            )
            error_row_instance.save()
            error_row_numbers.append(row.number)

    # Sort rows and attach the csv
    if error_row_numbers:
        error_row_numbers.sort()
        failed_row_csv_file = get_failed_rows_csv_file(
            import_job_instance, data, error_row_numbers
        )
        import_job_instance.failed_rows_csv = failed_row_csv_file
        import_job_instance.save()

    return report


def import_job(data, import_job_instance):
    logger = get_task_logger(__name__)

    resource = DictionaryEntryResource(
        site=import_job_instance.site,
        run_as_user=import_job_instance.run_as_user,
        import_job=import_job_instance.id,
    )

    try:
        import_resource(data, resource, import_job_instance, dry_run=False)
        import_job_instance.status = JobStatus.COMPLETE
    except Exception as e:
        logger.error(e)
        import_job_instance.status = JobStatus.FAILED
    finally:
        import_job_instance.save()


def import_job_dry_run(data, import_job_instance):
    """Variation of the import_job method above, for dry-run only.
    Updates the validationReport and validationStatus instead of the job status."""
    logger = get_task_logger(__name__)

    resource = DictionaryEntryResource(
        site=import_job_instance.site,
        run_as_user=import_job_instance.run_as_user,
        import_job=import_job_instance.id,
    )

    # Clearing out old report if present
    old_report = import_job_instance.validation_report
    if old_report:
        try:
            old_report = ImportJobReport.objects.filter(id=old_report.id)
            old_report.delete()
        except Exception as e:
            logger.error(e)
            import_job_instance.validation_status = JobStatus.FAILED
            return

    try:
        report = import_resource(data, resource, import_job_instance, dry_run=True)
        import_job_instance.validation_status = JobStatus.COMPLETE
        import_job_instance.validation_report = report
    except Exception as e:
        logger.error(e)
        import_job_instance.validation_status = JobStatus.FAILED


@shared_task
def batch_import_dry_run(import_job_instance_id):
    # Validates a provided CSV before importing provided entries
    logger = get_task_logger(__name__)
    task_id = current_task.request.id
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"import_job_instance_id: {import_job_instance_id}, dry-run: True",
    )

    import_job_instance = ImportJob.objects.get(id=import_job_instance_id)

    file = import_job_instance.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")

    # Checks to ensure consistency
    if import_job_instance.validation_status != JobStatus.ACCEPTED:
        raise ValidationError(
            "The specified job cannot be run due to consistency issues. "
            "Please try using the validate endpoint to try again."
        )

    if import_job_instance.status in [
        JobStatus.ACCEPTED,
        JobStatus.STARTED,
        JobStatus.COMPLETE,
    ]:
        raise ValidationError(
            "The specified job is either queued, or running or completed. "
            "Please create a new batch request to import the entries."
        )

    verify_no_other_import_jobs_running(import_job_instance)

    import_job_instance.validation_status = JobStatus.STARTED
    import_job_instance.validation_task_id = task_id

    import_job_dry_run(data, import_job_instance)
    import_job_instance.save()

    logger.info(ASYNC_TASK_END_TEMPLATE)


@shared_task
def batch_import(import_job_instance_id):
    logger = get_task_logger(__name__)
    task_id = current_task.request.id
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"import_job_instance_id: {import_job_instance_id}, dry-run: False",
    )

    import_job_instance = ImportJob.objects.get(id=import_job_instance_id)

    file = import_job_instance.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")

    # Do not start if the job is already queued
    if import_job_instance.status != JobStatus.ACCEPTED:
        raise ValidationError(
            "The specified job cannot be run due to consistency issues. "
            "Please try using the confirm endpoint to try again."
        )

    if import_job_instance.validation_status != JobStatus.COMPLETE:
        raise ValidationError("Please validate the job before confirming the import.")

    verify_no_other_import_jobs_running(import_job_instance)

    import_job_instance.status = JobStatus.STARTED
    import_job_instance.task_id = task_id

    import_job(data, import_job_instance)
    import_job_instance.save()

    logger.info(ASYNC_TASK_END_TEMPLATE)
