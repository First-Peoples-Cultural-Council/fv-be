from copy import deepcopy
from functools import reduce

import tablib
from celery import current_task, shared_task
from celery.utils.log import get_task_logger

from backend.importing.importers import (
    AudioImporter,
    DictionaryEntryImporter,
    DocumentImporter,
    ImageImporter,
    VideoImporter,
)
from backend.models.import_jobs import ImportJob, ImportJobMode, JobStatus
from backend.tasks.import_job_tasks import (
    attach_csv_to_report,
    generate_report,
    get_missing_referenced_entries,
    get_missing_referenced_media,
)
from backend.tasks.utils import (
    ASYNC_TASK_END_TEMPLATE,
    ASYNC_TASK_START_TEMPLATE,
    is_valid_header_variation,
    verify_no_other_import_jobs_running,
)


def get_valid_update_headers():
    importers = [
        AudioImporter,
        DocumentImporter,
        ImageImporter,
        VideoImporter,
        DictionaryEntryImporter,
    ]
    supported_columns = map(
        lambda importer: importer.get_supported_update_columns(), importers
    )
    return reduce(lambda a, b: a + b, supported_columns)


def clean_update_csv(
    data,
    missing_referenced_media=None,
    missing_entries=None,
):
    if missing_entries is None:
        missing_entries = []
    if missing_referenced_media is None:
        missing_referenced_media = []

    valid_headers = get_valid_update_headers()
    cleaned_data = deepcopy(data)
    all_headers = cleaned_data.headers
    accepted_headers = []
    invalid_headers = []

    for header in all_headers:
        if is_valid_header_variation(header, all_headers, valid_headers):
            accepted_headers.append(header.lower())
        else:
            invalid_headers.append(header)

    # Dropping invalid columns
    for invalid_header in invalid_headers:
        del cleaned_data[invalid_header]

    # lower-casing headers
    cleaned_data.headers = [header.lower() for header in cleaned_data.headers]

    # Remove rows that have missing media or entries
    missing_media_row_idx = [(obj["idx"] - 1) for obj in missing_referenced_media]
    missing_entries_row_idx = [(obj["idx"] - 1) for obj in missing_entries]

    rows_to_delete = {
        *missing_media_row_idx,
        *missing_entries_row_idx,
    }
    rows_to_delete = list(rows_to_delete)

    rows_to_delete.sort(reverse=True)
    for row_index in rows_to_delete:
        del cleaned_data[row_index]

    return accepted_headers, invalid_headers, cleaned_data


def process_update_job_data(data, update_job, dry_run=True):
    """
    Primary method that cleans the CSV data, uses resources to update models, and generates a report.
    Used for both dry_run and actual imports.
    """
    missing_referenced_media = get_missing_referenced_media(data, update_job.site.id)
    missing_entries = get_missing_referenced_entries(data, update_job.site.id)

    accepted_headers, invalid_headers, cleaned_data = clean_update_csv(
        data,
        missing_referenced_media=missing_referenced_media,
        missing_entries=missing_entries,
    )

    # import dictionary entries
    dictionary_entry_update_result = DictionaryEntryImporter.update_data(
        update_job, cleaned_data, dry_run
    )

    if dry_run:
        report = generate_report(
            import_job=update_job,
            accepted_columns=accepted_headers,
            ignored_columns=invalid_headers,
            missing_uploaded_media=[],
            missing_referenced_media=missing_referenced_media,
            missing_entries=missing_entries,
            audio_import_results=[],
            document_import_results=[],
            img_import_results=[],
            video_import_results=[],
            dictionary_entry_import_result=dictionary_entry_update_result,
        )
        attach_csv_to_report(data, update_job, report)


def run_update_job(data, update_job):
    """
    Executes the actual update operation (non dry-run mode) and updates the status attribute of the update job.
    """
    logger = get_task_logger(__name__)

    try:
        process_update_job_data(data, update_job, dry_run=False)
        update_job.status = JobStatus.COMPLETE
    except Exception as e:
        logger.error(e)
        update_job.status = JobStatus.FAILED
    finally:
        update_job.save()


def dry_run_update_job(data, update_job):
    """
    Performs a dry-run of the specified update job and updates the validation_status attribute of the update job.
    """
    logger = get_task_logger(__name__)

    try:
        process_update_job_data(data, update_job, dry_run=True)
        update_job.validation_status = JobStatus.COMPLETE
    except Exception as e:
        logger.error(e)
        update_job.validation_status = JobStatus.FAILED
    finally:
        update_job.save()


@shared_task
def validate_update_job(update_job_id):
    logger = get_task_logger(__name__)
    task_id = current_task.request.id
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"Update job id: {update_job_id}, dry-run: True",
    )

    update_job = ImportJob.objects.get(id=update_job_id, mode=ImportJobMode.UPDATE)

    file = update_job.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")

    # Checks to ensure consistency
    if update_job.validation_status != JobStatus.ACCEPTED:
        logger.info("This job cannot be run due to consistency issues.")
        update_job.validation_status = JobStatus.FAILED
        update_job.save()
        return

    if update_job.status in [
        JobStatus.ACCEPTED,
        JobStatus.STARTED,
        JobStatus.COMPLETE,
    ]:
        logger.info(
            "This job could not be started as it is either queued, or already running or completed. "
            f"Update job id: {update_job_id}."
        )
        update_job.validation_status = JobStatus.FAILED
        update_job.save()
        return

    verify_no_other_import_jobs_running(update_job)

    update_job.validation_status = JobStatus.STARTED
    update_job.validation_task_id = task_id

    dry_run_update_job(data, update_job)
    update_job.save()

    logger.info(ASYNC_TASK_END_TEMPLATE)


@shared_task
def confirm_update_job(update_job_id):
    logger = get_task_logger(__name__)
    task_id = current_task.request.id
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"Update job id: {update_job_id}, dry-run: False",
    )

    update_job = ImportJob.objects.get(id=update_job_id, mode=ImportJobMode.UPDATE)

    file = update_job.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")

    # Checks to ensure consistency
    if update_job.status != JobStatus.ACCEPTED:
        logger.info(
            f"This job cannot be run due to consistency issues. Update job id: {update_job_id}."
        )
        update_job.status = JobStatus.FAILED
        update_job.save()
        return

    if update_job.validation_status != JobStatus.COMPLETE:
        logger.info(
            f"Please validate the job before confirming the import. Update job id: {update_job_id}."
        )
        update_job.status = JobStatus.FAILED
        update_job.save()
        return

    verify_no_other_import_jobs_running(update_job)

    update_job.status = JobStatus.STARTED
    update_job.task_id = task_id

    run_update_job(data, update_job)
    update_job.save()

    logger.info(ASYNC_TASK_END_TEMPLATE)
