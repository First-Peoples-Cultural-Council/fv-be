from copy import deepcopy

import tablib
from celery import current_task, shared_task
from celery.utils.log import get_task_logger
from import_export.results import RowResult

from backend.models.files import File
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
    # audio
    "audio_filename",
    "audio_title",
    "audio_description",
    "audio_speaker",  # Add a new ticket for speaker support
    "audio_acknowledgement",
    "audio_include_in_kids_site",
    "audio_include_in_games",
    # image
    "img_filename",
    "img_title",
    "img_description",
    "img_acknowledgement",
    "img_include_in_kids_site",
    # video
    "video_filename",
    "video_title",
    "video_description",
    "video_acknowledgement",
    "video_include_in_kids_site",
    # video_embed_link to be added
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


def clean_csv(data, missing_media=[]):
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

    # Remove rows that have missing media
    rows_to_delete = [(obj["idx"] - 1) for obj in missing_media]
    rows_to_delete.sort(reverse=True)
    for row_index in rows_to_delete:
        del cleaned_data[row_index]

    return accepted_headers, invalid_headers, cleaned_data


def import_resource(data, import_job, missing_media=[], dry_run=True):
    accepted_columns, ignored_columns, cleaned_data = clean_csv(data, missing_media)

    # Create an ImportJobReport for the run
    report = ImportJobReport(
        site=import_job.site,
        importjob=import_job,
        accepted_columns=accepted_columns,
        ignored_columns=ignored_columns,
    )
    report.save()

    # media_import_result = MediaResources.import_data(dataset=cleaned_data, dry_run=dry_run)
    # Add media errors to report
    for missing_media_row in missing_media:
        error_row_instance = ImportJobReportRow(
            site=import_job.site,
            report=report,
            status=RowStatus.ERROR,
            row_number=missing_media_row["idx"],
            errors=[
                f"Media file not found in uploaded files: {missing_media_row['filename']}."
            ],
        )
        error_row_instance.save()

    # Import dictionary_entries
    dictionary_entry_import_result = DictionaryEntryResource(
        site=import_job.site,
        run_as_user=import_job.run_as_user,
        import_job=import_job.id,
    ).import_data(dataset=cleaned_data, dry_run=dry_run)

    # Adding error messages to the report
    for row in dictionary_entry_import_result.rows:
        if row.import_type == RowResult.IMPORT_TYPE_SKIP:
            error_row_instance = ImportJobReportRow(
                site=import_job.site,
                report=report,
                status=RowStatus.ERROR,
                row_number=row.number,
                errors=row.error_messages,
            )
            error_row_instance.save()

    report.new_rows = dictionary_entry_import_result.totals[
        "new"
    ]  # + media_import_result.new_rows
    report.error_rows = ImportJobReportRow.objects.filter(report=report).count()
    report.save()

    # Sort rows and attach the csv
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
    else:
        # Clearing up failed rows csv, incase it exists, and there are no errors present
        import_job.failed_rows_csv = None

    return report


def run_import_job(data, import_job):
    logger = get_task_logger(__name__)

    try:
        import_resource(data, import_job, dry_run=False)
        import_job.status = JobStatus.COMPLETE
    except Exception as e:
        logger.error(e)
        import_job.status = JobStatus.FAILED
    finally:
        import_job.save()


def dry_run_import_job(data, import_job):
    """Variation of the import_job method above, for dry-run only.
    Updates the validationReport and validationStatus instead of the job status."""
    logger = get_task_logger(__name__)

    missing_media = get_missing_media(data, import_job)

    # Clearing out old report if present
    old_report = import_job.validation_report
    if old_report:
        try:
            old_report = ImportJobReport.objects.filter(id=old_report.id)
            old_report.delete()
        except Exception as e:
            logger.error(e)
            import_job.validation_status = JobStatus.FAILED
            return

    try:
        report = import_resource(data, import_job, missing_media, dry_run=True)
        import_job.validation_status = JobStatus.COMPLETE
        import_job.validation_report = report
    except Exception as e:
        logger.error(e)
        import_job.validation_status = JobStatus.FAILED
    finally:
        import_job.save()


def get_missing_media(data, import_job_instance):
    missing_media = []
    associated_files = list(
        File.objects.filter(import_job=import_job_instance).values_list(
            "content", flat=True
        )
    )
    associated_filenames = [file.split("/")[-1] for file in associated_files]

    # Audio
    if "AUDIO_FILENAME" in data.headers:
        for idx, filename in enumerate(data["AUDIO_FILENAME"]):
            if filename and filename not in associated_filenames:
                missing_media.append({"idx": idx + 1, "filename": filename})

    # Image
    if "IMG_FILENAME" in data.headers:
        for idx, filename in enumerate(data["IMG_FILENAME"]):
            if filename and filename not in associated_filenames:
                missing_media.append({"idx": idx + 1, "filename": filename})

    # Video
    if "VIDEO_FILENAME" in data.headers:
        for idx, filename in enumerate(data["VIDEO_FILENAME"]):
            if filename and filename not in associated_filenames:
                missing_media.append({"idx": idx + 1, "filename": filename})

    return missing_media


@shared_task
def validate_import_job(import_job_id):
    # Validates a provided CSV before importing provided entries
    logger = get_task_logger(__name__)
    task_id = current_task.request.id
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"ImportJob id: {import_job_id}, dry-run: True",
    )

    import_job = ImportJob.objects.get(id=import_job_id)

    file = import_job.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")

    # Checks to ensure consistency
    if import_job.validation_status != JobStatus.ACCEPTED:
        logger.info("This job cannot be run due to consistency issues.")
        import_job.validation_status = JobStatus.FAILED
        import_job.save()
        return

    if import_job.status in [
        JobStatus.ACCEPTED,
        JobStatus.STARTED,
        JobStatus.COMPLETE,
    ]:
        logger.info(
            "This job could not be started as it is either queued, or already running or completed. "
            f"ImportJob id: {import_job_id}."
        )
        import_job.validation_status = JobStatus.FAILED
        import_job.save()
        return

    verify_no_other_import_jobs_running(import_job)

    import_job.validation_status = JobStatus.STARTED
    import_job.validation_task_id = task_id

    dry_run_import_job(data, import_job)
    import_job.save()

    logger.info(ASYNC_TASK_END_TEMPLATE)


@shared_task
def confirm_import_job(import_job_id):
    logger = get_task_logger(__name__)
    task_id = current_task.request.id
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"ImportJob id: {import_job_id}, dry-run: False",
    )

    import_job = ImportJob.objects.get(id=import_job_id)

    file = import_job.data.content.open().read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")

    # Do not start if the job is already queued
    if import_job.status != JobStatus.ACCEPTED:
        logger.info(
            f"This job cannot be run due to consistency issues. ImportJob id: {import_job_id}."
        )
        import_job.status = JobStatus.FAILED
        import_job.save()

    if import_job.validation_status != JobStatus.COMPLETE:
        logger.info(
            f"Please validate the job before confirming the import. ImportJob id: {import_job_id}."
        )
        import_job.validation_status = JobStatus.FAILED
        import_job.save()

    verify_no_other_import_jobs_running(import_job)

    import_job.status = JobStatus.STARTED
    import_job.task_id = task_id

    run_import_job(data, import_job)
    import_job.save()

    logger.info(ASYNC_TASK_END_TEMPLATE)
