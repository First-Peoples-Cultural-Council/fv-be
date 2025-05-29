from copy import deepcopy

import tablib
from celery import current_task, shared_task
from celery.utils.log import get_task_logger
from django.utils.text import get_valid_filename
from import_export.results import RowResult

from backend.importing.importers import AudioImporter, ImageImporter, VideoImporter
from backend.models.files import File
from backend.models.import_jobs import (
    ImportJob,
    ImportJobReport,
    ImportJobReportRow,
    JobStatus,
)
from backend.models.media import ImageFile, VideoFile
from backend.resources.dictionary import DictionaryEntryResource
from backend.tasks.utils import (
    ASYNC_TASK_END_TEMPLATE,
    ASYNC_TASK_START_TEMPLATE,
    VALID_HEADERS,
    create_or_append_error_row,
    get_failed_rows_csv_file,
    is_valid_header_variation,
    verify_no_other_import_jobs_running,
)


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
    rows_to_delete = list({(obj["idx"] - 1) for obj in missing_media})
    rows_to_delete.sort(reverse=True)
    for row_index in rows_to_delete:
        del cleaned_data[row_index]

    return accepted_headers, invalid_headers, cleaned_data


def separate_datasets(data):
    """
    Splits the cleaned CSV data into four datasets:
    - Dictionary entries
    - Filtered audio entries
    - Filtered image entries
    - Filtered video resources
    """
    # Building filtered datasets for media
    filtered_audio_data = AudioImporter.filter_data(data)
    filtered_img_data = ImageImporter.filter_data(data)
    filtered_video_data = VideoImporter.filter_data(data)

    # Building dataset for dictionary entries
    media_supported_columns = (
        AudioImporter.supported_columns
        + ImageImporter.supported_columns
        + VideoImporter.supported_columns
    )
    media_columns = [col for col in media_supported_columns if col in data.headers]
    exclude_columns = set(media_columns)
    keep_columns = [
        col
        for col in data.headers
        if col not in exclude_columns
        or col in ["audio_filename", "img_filename", "video_filename"]
    ]
    dictionary_entries_data = tablib.Dataset(headers=keep_columns)

    for row in data.dict:
        dictionary_entries_row = [row[col] for col in keep_columns]
        dictionary_entries_data.append(dictionary_entries_row)

    return (
        dictionary_entries_data,
        filtered_audio_data,
        filtered_img_data,
        filtered_video_data,
    )


def get_column_index(data, column_name):
    """
    Return the index of column if present in the dataset.
    """
    try:
        column_index = data.headers.index(column_name)
        return column_index
    except ValueError:
        return -1


def add_column(data, column_name):
    """
    Add provided column to the tablib dataset.
    """
    data.append_col([""] * len(data), header=column_name)
    return data.headers.index(column_name)


def add_related_id(row_list, filename_col_index, related_media_col_index, media_map):
    """
    Lookup the filename against the media map, and add the id of the media resource to
    the provided row.
    """
    if not media_map:
        # If media map is empty, do nothing
        return

    filename = row_list[filename_col_index]
    related_id = media_map.get(filename, "")
    row_list[related_media_col_index] = related_id


def import_dictionary_entry_resource(
    import_job,
    dictionary_entry_data,
    audio_filename_map,
    img_filename_map,
    video_filename_map,
    dry_run,
):
    """
    Imports dictionary entries and returns the import result.
    This method adds related media columns, i.e. "related_images", "related_audio" and fills
    them up with ids from the media maps, by looking them up against the filename columns.
    """

    related_audio_column = add_column(dictionary_entry_data, "related_audio")
    audio_filename_column = get_column_index(dictionary_entry_data, "audio_filename")
    related_image_column = add_column(dictionary_entry_data, "related_images")
    image_filename_column = get_column_index(dictionary_entry_data, "img_filename")
    related_video_column = add_column(dictionary_entry_data, "related_videos")
    video_filename_column = get_column_index(dictionary_entry_data, "video_filename")

    for i, row in enumerate(dictionary_entry_data.dict):
        row_list = list(dictionary_entry_data[i])
        add_related_id(
            row_list, audio_filename_column, related_audio_column, audio_filename_map
        )
        add_related_id(
            row_list, image_filename_column, related_image_column, img_filename_map
        )
        add_related_id(
            row_list, video_filename_column, related_video_column, video_filename_map
        )
        dictionary_entry_data[i] = tuple(row_list)

    dictionary_entry_import_result = DictionaryEntryResource(
        site=import_job.site,
        run_as_user=import_job.run_as_user,
        import_job=import_job.id,
    ).import_data(dataset=dictionary_entry_data, dry_run=dry_run)

    return dictionary_entry_import_result


def generate_report(
    import_job,
    accepted_columns,
    ignored_columns,
    missing_media,
    audio_import_result,
    img_import_result,
    video_import_result,
    dictionary_entry_import_result,
):
    """
    Creates an ImportJobReport to summarize the results.
    Also combines rows from missing_media, audio import and dictionary entries import.
    """
    report = ImportJobReport(
        site=import_job.site,
        importjob=import_job,
        accepted_columns=accepted_columns,
        ignored_columns=ignored_columns,
    )
    report.save()

    # Add media errors to report
    for missing_media_row in missing_media:
        create_or_append_error_row(
            import_job,
            report,
            row_number=missing_media_row["idx"],
            errors=[
                f"Media file not found in uploaded files: {missing_media_row['filename']}."
            ],
        )

    # Add errors from individual import results to report
    for result in [
        dictionary_entry_import_result,
        audio_import_result,
        img_import_result,
        video_import_result,
    ]:
        for row in result.rows:
            if row.import_type == RowResult.IMPORT_TYPE_SKIP:
                create_or_append_error_row(
                    import_job, report, row_number=row.number, errors=row.error_messages
                )

    report.new_rows = dictionary_entry_import_result.totals["new"]
    report.error_rows = ImportJobReportRow.objects.filter(report=report).count()
    report.save()

    return report


def attach_csv_to_report(data, import_job, report):
    """
    Attaches an updated CSV file to the importJob if any errors occurred.
    """
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


def process_import_job_data(data, import_job, missing_media=[], dry_run=True):
    """
    Primary method that cleans the CSV data, separates it, imports resources, and generates a report.
    Used for both dry_run and actual imports.
    """

    accepted_columns, ignored_columns, cleaned_data = clean_csv(data, missing_media)

    # get a separate table for each model
    dictionary_entry_data, audio_data, img_data, video_data = separate_datasets(
        cleaned_data
    )

    audio_import_result, audio_filename_map = AudioImporter.import_data(
        import_job, audio_data, dry_run
    )
    img_import_result, img_filename_map = ImageImporter.import_data(
        import_job, img_data, dry_run
    )
    video_import_result, video_filename_map = VideoImporter.import_data(
        import_job, video_data, dry_run
    )

    dictionary_entry_import_result = import_dictionary_entry_resource(
        import_job,
        dictionary_entry_data,
        audio_filename_map,
        img_filename_map,
        video_filename_map,
        dry_run,
    )

    report = generate_report(
        import_job,
        accepted_columns,
        ignored_columns,
        missing_media,
        audio_import_result,
        img_import_result,
        video_import_result,
        dictionary_entry_import_result,
    )
    attach_csv_to_report(data, import_job, report)

    return report


def run_import_job(data, import_job):
    """
    Executes the actual import (non dry-run mode) amd update the status attribute of import-job.
    """
    logger = get_task_logger(__name__)

    try:
        process_import_job_data(data, import_job, dry_run=False)
        import_job.status = JobStatus.COMPLETE
    except Exception as e:
        logger.error(e)
        import_job.status = JobStatus.FAILED
    finally:
        import_job.save()


def dry_run_import_job(data, import_job):
    """
    Performs a dry-run of the specified import-job and update the validation_status attribute of import-job.
    """
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
        report = process_import_job_data(data, import_job, missing_media, dry_run=True)
        import_job.validation_status = JobStatus.COMPLETE
        import_job.validation_report = report
    except Exception as e:
        logger.error(e)
        import_job.validation_status = JobStatus.FAILED
    finally:
        import_job.save()


def get_missing_media(data, import_job_instance):
    """
    Checks for missing media files in the specified import-job by comparing file names present in the data
    with the uploaded files associated with the import-job.
    Returns a list of missing media files.
    """
    associated_audio_files = list(
        File.objects.filter(import_job=import_job_instance).values_list(
            "content", flat=True
        )
    )
    associated_video_files = list(
        VideoFile.objects.filter(import_job=import_job_instance).values_list(
            "content", flat=True
        )
    )
    associated_image_files = list(
        ImageFile.objects.filter(import_job=import_job_instance).values_list(
            "content", flat=True
        )
    )
    associated_files = (
        associated_image_files + associated_video_files + associated_audio_files
    )

    associated_filenames = [file.split("/")[-1] for file in associated_files]

    missing_media = []
    media_fields = ["AUDIO_FILENAME", "IMG_FILENAME", "VIDEO_FILENAME"]

    for field in media_fields:
        if field not in data.headers:
            continue
        for idx, filename in enumerate(data[field]):
            if not filename:
                # Do nothing if the field is empty
                continue
            valid_filename = get_valid_filename(filename)
            if valid_filename not in associated_filenames:
                # If a filename is provided, but the file cannot be found in the associated files
                # add an error row for that in missing media
                missing_media.append({"idx": idx + 1, "filename": filename})

    return missing_media


@shared_task
def validate_import_job(import_job_id):
    """
    Performs validation on the uploaded CSV file, and does a dry-run of the process to
    identify any errors such as missing fields, incorrect data, or missing media.
    Generates and attaches a report to the import-job for review.
    """

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
    """
    Schedules the actual import for the import-job.
    Can be used only after the import-job is successfully validated.
    """
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
