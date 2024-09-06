import io
import sys
from copy import deepcopy

import tablib
from celery import current_task, shared_task
from celery.utils.log import get_task_logger
from django.core.files.uploadedfile import InMemoryUploadedFile
from import_export.results import RowResult

from backend.models.import_jobs import (
    ImportJob,
    ImportJobReport,
    ImportJobReportRow,
    JobStatus,
    RowStatus,
)
from backend.models.media import File
from backend.resources.dictionary import DictionaryEntryResource
from backend.tasks.utils import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE

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


def get_failed_rows_csv_file(import_job_instance, data, error_row_numbers):
    # Generate a csv for the erroneous rows
    failed_row_dataset = []
    for row_num in error_row_numbers:
        failed_row_dataset.append(
            data[row_num - 1]
        )  # -1 to subtract to account for headers
    failed_row_dataset = tablib.Dataset(*failed_row_dataset)
    failed_row_dataset.headers = data.headers

    failed_row_export = failed_row_dataset.export("csv")
    in_memory_csv_file = io.BytesIO(failed_row_export.encode("utf-8"))
    in_memory_csv_file = InMemoryUploadedFile(
        file=in_memory_csv_file,
        field_name="failed_rows_csv",
        name="failed_rows.csv",
        content_type="text/csv",
        size=sys.getsizeof(in_memory_csv_file),
        charset="utf-8",
    )
    failed_row_csv_file = File(
        content=in_memory_csv_file,
        site=import_job_instance.site,
        created_by=import_job_instance.last_modified_by,
        last_modified_by=import_job_instance.last_modified_by,
    )
    failed_row_csv_file.save()
    return failed_row_csv_file


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
        skipped_rows=0,
        error_rows=result.totals["error"] + result.totals["invalid"] + result.totals["skip"],
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

    error_row_numbers.sort()

    # Attach the csv
    failed_row_csv_file = get_failed_rows_csv_file(
        import_job_instance, data, error_row_numbers
    )
    import_job_instance.failed_rows_csv = failed_row_csv_file
    import_job_instance.save()

    return report


def import_job(data, import_job_instance, logger):
    resource = DictionaryEntryResource(site=import_job_instance.site)

    try:
        import_resource(data, resource, import_job_instance, dry_run=False)
        import_job_instance.status = JobStatus.COMPLETE
    except Exception as e:
        logger.error(e)
        import_job_instance.status = JobStatus.FAILED


def import_job_dry_run(data, import_job_instance, logger):
    """Variation of the import_job method above, for dry-run only.
    Updates the validationReport and validationStatus instead of the job status."""
    resource = DictionaryEntryResource(site=import_job_instance.site)

    try:
        report = import_resource(data, resource, import_job_instance, dry_run=True)
        import_job_instance.validation_status = JobStatus.COMPLETE
        import_job_instance.validation_report = report
    except Exception as e:
        logger.error(e)
        import_job_instance.validation_status = JobStatus.FAILED


@shared_task
def batch_import(import_job_instance_id, dry_run=True):
    # This method passes the provided CSV file through the clean method,
    # does a dry-run or the import as per the dry_run flag provided,
    # then parses through the result to return a validation report.

    logger = get_task_logger(__name__)
    task_id = current_task.request.id
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"import_job_instance_id: {import_job_instance_id}, dry-run: {dry_run}",
    )

    import_job_instance = ImportJob.objects.get(id=import_job_instance_id)

    # Assert conditions to verify no other job is running.
    # If any variation of an import job is currently running for the provided site,
    # abort the task and provide an error message.

    site = import_job_instance.site

    # Get any incomplete jobs, except for the currently specified one.
    existing_incomplete_import_jobs = ImportJob.objects.filter(
        site=site, status=JobStatus.STARTED
    ).exclude(id=import_job_instance.id)

    if len(existing_incomplete_import_jobs):
        logger.error(
            "There is at least 1 already on-going job on this site. "
            "Please wait for it to finish before starting a new one."
        )
        logger.info(ASYNC_TASK_END_TEMPLATE)
        import_job_instance.status = JobStatus.CANCELLED
        import_job_instance.save()
        return

    # If the job status is already completed, also abort the task
    if import_job_instance.status in [JobStatus.COMPLETE, JobStatus.FAILED]:
        logger.error(
            "The job has already been executed once. "
            "Please create another batch request to import the entries."
        )
        logger.info(ASYNC_TASK_END_TEMPLATE)
        return

    # If dry-run has not been executed successfully, do not proceed
    if (dry_run is False) and (
        import_job_instance.validation_status != JobStatus.COMPLETE
    ):
        logger.error(
            "A successful dry-run is required before doing the import. "
            "Please fix any issues found during the dry-run of the CSV file and run a new batch."
        )
        logger.info(ASYNC_TASK_END_TEMPLATE)

        import_job_instance.status = JobStatus.CANCELLED
        import_job_instance.save()
        return

    if dry_run:
        import_job_instance.validation_task_id = task_id
        import_job_instance.validation_status = JobStatus.STARTED
        import_job_instance.save()

    file = import_job_instance.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")

    if dry_run:
        import_job_dry_run(data, import_job_instance, logger)
    else:
        import_job(data, import_job_instance, logger)

    import_job_instance.save()
    logger.info(ASYNC_TASK_END_TEMPLATE)
