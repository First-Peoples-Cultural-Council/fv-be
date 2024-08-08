import tablib
from celery import current_task, shared_task
from celery.utils.log import get_task_logger

from backend.models.import_jobs import (
    ImportJob,
    ImportJobReport,
    ImportJobReportRow,
    JobStatus,
    RowStatus,
)
from backend.models.sites import SiteFeature
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
        del data[invalid_header]

    return accepted_headers, invalid_headers, data


@shared_task
def batch_import_dry_run(import_job_instance_id):
    # This method is used to dry-run the CSV file for a bulk import later.
    # Passes the provided CSV file through the clean method, tries uploading it
    # parses through the result to return a validation report.
    logger = get_task_logger(__name__)
    task_id = current_task.request.id

    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"import_job_instance_id: {import_job_instance_id}, dry-run: True",
    )

    import_job_instance = ImportJob.objects.get(id=import_job_instance_id)

    # If any variation of an import job is currently running for the provided site,
    # abort the task and provide an error message.
    site = import_job_instance.site
    existing_incomplete_import_jobs = ImportJob.objects.filter(
        site=site, status=JobStatus.STARTED
    )

    if len(existing_incomplete_import_jobs):
        import_job_instance.status = JobStatus.CANCELLED
        import_job_instance.save()

        # Should we raise a exception here or just log and return ?
        logger.error(
            "There is at least 1 already on-going job on this site. "
            "Please wait for it to finish before starting a new one."
        )
        logger.info(ASYNC_TASK_END_TEMPLATE)
        return

    # The job status is already completed, also abort the task
    if import_job_instance.status in [JobStatus.COMPLETE, JobStatus.FAILED]:
        import_job_instance.status = JobStatus.CANCELLED
        import_job_instance.save()

        logger.error(
            "The job has already been executed once. "
            "Please create another batch request to import the entries."
        )
        logger.info(ASYNC_TASK_END_TEMPLATE)
        return

    import_job_instance.validation_task_id = task_id
    import_job_instance.validation_status = JobStatus.STARTED
    import_job_instance.save()

    file = import_job_instance.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")
    accepted_columns, ignored_columns, cleaned_data = clean_csv(data)

    resource = DictionaryEntryResource(site=import_job_instance.site)

    try:
        result = resource.import_data(dataset=cleaned_data, dry_run=True)

        # Create an ImportJobReport for the run
        report = ImportJobReport(
            site=import_job_instance.site,
            importjob=import_job_instance,
            new_rows=result.totals["new"],
            skipped_rows=result.totals["skip"],
            error_rows=result.totals["error"] + result.totals["invalid"],
            accepted_columns=accepted_columns,
            ignored_columns=ignored_columns,
        )
        report.save()

        import_job_instance.validation_status = JobStatus.COMPLETE
        import_job_instance.validation_report = report
        import_job_instance.save()

        # check for errors
        if result.has_errors():
            for row in result.error_rows:
                error_messages = []
                for error_row in row.errors:
                    first_line = str(error_row.error).split("\n")[0]
                    error_messages.append(first_line)
                error_row_instance = ImportJobReportRow(
                    site=import_job_instance.site,
                    report=report,
                    status=RowStatus.ERROR,
                    row_number=row.number,
                    errors=error_messages,
                )
                error_row_instance.save()

        # Check for invalid rows
        if len(result.invalid_rows):
            for row in result.invalid_rows:
                error_row_instance = ImportJobReportRow(
                    site=import_job_instance.site,
                    report=report,
                    status=RowStatus.ERROR,
                    row_number=row.number,
                    errors=row.error.messages,
                )
                error_row_instance.save()
    except Exception as e:
        import_job_instance.status = JobStatus.FAILED
        import_job_instance.save()

        logger.error(e)

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

    # If any variation of an import job is currently running for the provided site,
    # abort the task and provide an error message.
    site = import_job_instance.site
    existing_incomplete_import_jobs = ImportJob.objects.filter(
        site=site, status=JobStatus.STARTED
    )

    if len(existing_incomplete_import_jobs):
        import_job_instance.status = JobStatus.CANCELLED
        import_job_instance.save()

        # Should we raise a exception here or just log and return ?
        logger.error(
            "There is at least 1 already on-going job on this site. "
            "Please wait for it to finish before starting a new one."
        )
        logger.info(ASYNC_TASK_END_TEMPLATE)
        return

    # The job status is already completed, also abort the task
    if import_job_instance.status in [JobStatus.COMPLETE, JobStatus.FAILED]:
        import_job_instance.status = JobStatus.CANCELLED
        import_job_instance.save()

        logger.error(
            "The job has already been executed once. "
            "Please create another batch request to import the entries."
        )
        logger.info(ASYNC_TASK_END_TEMPLATE)
        return

    import_job_instance.task_id = task_id
    import_job_instance.status = JobStatus.STARTED
    import_job_instance.save()

    file = import_job_instance.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")
    accepted_columns, ignored_columns, cleaned_data = clean_csv(data)

    # After a batch has been successfully uploaded, we should run a re-index for the site

    # Disconnecting search indexing signals
    indexing_paused_feature = SiteFeature.objects.get_or_create(
        site=site, key="indexing_paused"
    )
    indexing_paused_feature[0].is_enabled = True
    indexing_paused_feature[0].save()

    logger.info(f"Indexing paused for site: {import_job_instance.site}.")

    resource = DictionaryEntryResource(site=import_job_instance.site)

    try:
        result = resource.import_data(dataset=cleaned_data, dry_run=False)

        # Create an ImportJobReport for the run
        report = ImportJobReport(
            site=import_job_instance.site,
            importjob=import_job_instance,
            new_rows=result.totals["new"],
            skipped_rows=result.totals["skip"],
            error_rows=result.totals["error"] + result.totals["invalid"],
            accepted_columns=accepted_columns,
            ignored_columns=ignored_columns,
        )
        report.save()

        import_job_instance.status = JobStatus.COMPLETE
        import_job_instance.save()

        # check for errors
        if result.has_errors():
            for row in result.error_rows:
                error_messages = []
                for error_row in row.errors:
                    first_line = str(error_row.error).split("\n")[0]
                    error_messages.append(first_line)
                error_row_instance = ImportJobReportRow(
                    site=import_job_instance.site,
                    report=report,
                    status=RowStatus.ERROR,
                    row_number=row.number,
                    errors=error_messages,
                )
                error_row_instance.save()

        # Check for invalid rows
        if len(result.invalid_rows):
            for row in result.invalid_rows:
                error_row_instance = ImportJobReportRow(
                    site=import_job_instance.site,
                    report=report,
                    status=RowStatus.ERROR,
                    row_number=row.number,
                    errors=row.error.messages,
                )
                error_row_instance.save()
    except Exception as e:
        import_job_instance.status = JobStatus.FAILED
        import_job_instance.save()

        logger.error(e)

    # Connecting back search indexing signals
    indexing_paused_feature[0].is_enabled = False
    indexing_paused_feature[0].save()

    logger.info(f"Indexing now resumed for site: {import_job_instance.site}.")

    logger.info(ASYNC_TASK_END_TEMPLATE)
