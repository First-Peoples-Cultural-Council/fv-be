from copy import deepcopy
from functools import reduce

import tablib
from celery import current_task, shared_task
from celery.utils.log import get_task_logger
from django.utils.text import get_valid_filename
from import_export.results import RowResult

from backend.importing.importers import (
    AudioImporter,
    DictionaryEntryImporter,
    ImageImporter,
    VideoImporter,
)
from backend.models.dictionary import DictionaryEntry, DictionaryEntryLink
from backend.models.files import File
from backend.models.import_jobs import (
    ImportJob,
    ImportJobReport,
    ImportJobReportRow,
    JobStatus,
)
from backend.models.media import ImageFile, VideoFile
from backend.tasks.utils import (
    ASYNC_TASK_END_TEMPLATE,
    ASYNC_TASK_START_TEMPLATE,
    create_or_append_error_row,
    get_failed_rows_csv_file,
    is_valid_header_variation,
    verify_no_other_import_jobs_running,
)


def get_valid_headers():
    importers = [AudioImporter, ImageImporter, VideoImporter, DictionaryEntryImporter]
    supported_columns = map(
        lambda importer: importer.get_supported_columns(), importers
    )
    return reduce(lambda a, b: a + b, supported_columns)


def clean_csv(
    data,
    missing_uploaded_media=None,
    missing_referenced_media=None,
    missing_entries=None,
):
    """
    Method to run validations on a csv file and returns a list of
    accepted columns, ignored columns and a cleaned csv for importing.
    This method also drops the ignored columns as those will not be used during import.
    """
    if missing_uploaded_media is None:
        missing_uploaded_media = []
    if missing_referenced_media is None:
        missing_referenced_media = []
    if missing_entries is None:
        missing_entries = []

    valid_headers = get_valid_headers()
    cleaned_data = deepcopy(data)  # so we keep an original copy for return purposes
    all_headers = data.headers
    accepted_headers = []
    invalid_headers = []

    # If any invalid headers are present, skip them and raise a warning
    for header in all_headers:
        if is_valid_header_variation(header, all_headers, valid_headers):
            accepted_headers.append(header)
        else:
            invalid_headers.append(header)

    # Dropping invalid columns
    for invalid_header in invalid_headers:
        del cleaned_data[invalid_header]

    # lower-casing headers
    cleaned_data.headers = [header.lower() for header in cleaned_data.headers]

    # Remove rows that have missing media or entries
    missing_media_row_idx = [(obj["idx"] - 1) for obj in missing_uploaded_media]
    missing_referenced_media_row_idx = [
        (obj["idx"] - 1) for obj in missing_referenced_media
    ]
    missing_entries_row_idx = [(obj["idx"] - 1) for obj in missing_entries]

    rows_to_delete = {
        *missing_media_row_idx,
        *missing_referenced_media_row_idx,
        *missing_entries_row_idx,
    }
    rows_to_delete = list(rows_to_delete)

    rows_to_delete.sort(reverse=True)
    for row_index in rows_to_delete:
        del cleaned_data[row_index]

    return accepted_headers, invalid_headers, cleaned_data


def append_missing_from_entry_data(
    idx, row, failed_related_entry_data, related_entry_headers
):
    """
    If a row does not have an ID (i.e. was not imported), append it to the failed_link_entry_list
    to indicate that related entries could not be linked for this row.
    """
    for header in related_entry_headers:
        if row.get(header):
            failed_related_entry_data.append(
                {
                    "idx": idx,
                    "title": row.get("title"),
                    "type": "from_entry",
                    "related_entry_title": row.get(header),
                }
            )


def link_related_entries(from_entry, to_entry):
    """
    Creates a link between two dictionary entries, avoiding self-referential or duplicate links.
    """
    if from_entry.id == to_entry.id:
        return

    if DictionaryEntryLink.objects.filter(
        from_dictionary_entry=from_entry, to_dictionary_entry=to_entry
    ).exists():
        return

    DictionaryEntryLink.objects.create(
        from_dictionary_entry=from_entry,
        to_dictionary_entry=to_entry,
    )


def handle_related_entries(import_data, entry_title_map, dry_run):
    """
    Links related dictionary entries by title based on the RELATED_ENTRY columns in the CSV data.
    Any errors encountered during the linking process are added to failed_related_entry_data.
    """

    related_entry_headers = [
        header
        for header in import_data.headers
        if header.lower().startswith("related_entry")
    ]
    if not related_entry_headers:
        return []

    failed_related_entry_data = []

    for idx, row in enumerate(import_data.dict):

        # Skip rows without an ID as these entries have not been imported
        if not row["id"]:
            append_missing_from_entry_data(
                idx + 1, row, failed_related_entry_data, related_entry_headers
            )

        for related_entry_header in related_entry_headers:
            related_entry_title = row[related_entry_header]
            if not related_entry_title:
                # No related entry specified in this column, skip
                continue

            related_entry_id = entry_title_map.get(related_entry_title)

            # Related entry not found in the imported entries
            if not related_entry_id:
                failed_related_entry_data.append(
                    {
                        "idx": idx + 1,
                        "title": related_entry_title,
                        "type": "to_entry",
                        "related_entry_title": row.get("title"),
                    }
                )
                continue

            if not dry_run:
                from_entry = DictionaryEntry.objects.get(id=row["id"])
                to_entry = DictionaryEntry.objects.get(id=related_entry_id)
                link_related_entries(from_entry, to_entry)

    return failed_related_entry_data


def generate_report(
    import_job,
    accepted_columns,
    ignored_columns,
    missing_uploaded_media,
    missing_referenced_media,
    missing_entries,
    audio_import_results,
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

    # Add media errors to report
    for missing_media_row in missing_uploaded_media:
        create_or_append_error_row(
            import_job,
            report,
            row_number=missing_media_row["idx"],
            error_message=[
                f"Media file missing in uploaded files: "
                f"{missing_media_row['filename']}, column: {missing_media_row['column']}."
            ],
        )

    # Add media errors to report
    for missing_media_id_row in missing_referenced_media:
        create_or_append_error_row(
            import_job,
            report,
            row_number=missing_media_id_row["idx"],
            error_message=[
                f"Referenced media not found for "
                f"ID: {missing_media_id_row['id']} in column: {missing_media_id_row['column']}."
            ],
        )

    # Add entry ID errors to report
    for missing_entry_row in missing_entries:
        create_or_append_error_row(
            import_job,
            report,
            row_number=missing_entry_row["idx"],
            error_message=[
                f"Referenced dictionary entry not found for ID: {missing_entry_row['id']}"
            ],
        )

    # Add errors from individual import results to report
    all_results = (
        [dictionary_entry_import_result]
        + audio_import_results
        + img_import_results
        + video_import_results
    )
    for result in all_results:
        for row in result.rows:
            if row.import_type == RowResult.IMPORT_TYPE_SKIP:
                create_or_append_error_row(
                    import_job,
                    report,
                    row_number=row.number,
                    error_message=row.error_messages,
                )

    report.new_rows = dictionary_entry_import_result.totals["new"]
    report.error_rows = ImportJobReportRow.objects.filter(report=report).count()
    report.save()

    return report


def add_missing_related_entry_errors(
    entry_title_map, failed_related_entry_data, import_job, report
):
    """
    Appends missing related entry errors to the report for any related entries that could not be linked.
    """

    if not failed_related_entry_data:
        return

    for data in failed_related_entry_data:
        related_entry_id = (
            entry_title_map.get(data["related_entry_title"])
            or "N/A: entry not imported"
        )
        if data["type"] == "from_entry":
            error_message = (
                f"Entry '{data['title']}' was not imported, and could not be linked as a "
                f"related entry to entry '{data['related_entry_title']}' with ID '{related_entry_id}'. "
                f"Please link the entries manually after re-importing the missing entry."
            )
            create_or_append_error_row(
                import_job, report, data["idx"], str(error_message)
            )

        else:
            error_message = (
                f"Related entry '{data['title']}' could not be found to link to entry '{data['related_entry_title']}' "
                f"with ID '{related_entry_id}'. Please link the entries manually after re-importing the missing entry."
            )
            create_or_append_error_row(
                import_job, report, data["idx"], str(error_message)
            )


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


def process_import_job_data(
    data,
    import_job,
    missing_uploaded_media=[],
    missing_referenced_media=[],
    dry_run=True,
):
    """
    Primary method that cleans the CSV data, imports resources, and generates a report.
    Used for both dry_run and actual imports.
    """
    missing_entries = get_missing_referenced_entries(data, import_job.site.id)

    accepted_columns, ignored_columns, cleaned_data = clean_csv(
        data, missing_uploaded_media, missing_referenced_media, missing_entries
    )

    # import media first
    audio_import_results, audio_filename_map = AudioImporter.import_data(
        import_job, cleaned_data, dry_run
    )
    img_import_results, img_filename_map = ImageImporter.import_data(
        import_job, cleaned_data, dry_run
    )
    video_import_results, video_filename_map = VideoImporter.import_data(
        import_job, cleaned_data, dry_run
    )

    # import dictionary entries
    dictionary_entry_import_result, entry_title_map, import_data = (
        DictionaryEntryImporter.import_data(
            import_job,
            cleaned_data,
            dry_run,
            audio_filename_map,
            img_filename_map,
            video_filename_map,
        )
    )

    failed_related_entry_data = handle_related_entries(
        import_data, entry_title_map, dry_run
    )

    if dry_run:
        report = generate_report(
            import_job,
            accepted_columns,
            ignored_columns,
            missing_uploaded_media,
            missing_referenced_media,
            missing_entries,
            audio_import_results,
            img_import_results,
            video_import_results,
            dictionary_entry_import_result,
        )
        add_missing_related_entry_errors(
            entry_title_map, failed_related_entry_data, import_job, report
        )
        attach_csv_to_report(data, import_job, report)


def run_import_job(data, import_job):
    """
    Executes the actual import (non dry-run mode) amd update the status attribute of import-job.
    """
    logger = get_task_logger(__name__)

    missing_uploaded_media = get_missing_uploaded_media(data, import_job)
    missing_referenced_media = get_missing_referenced_media(data, import_job.site.id)

    try:
        process_import_job_data(
            data,
            import_job,
            missing_uploaded_media,
            missing_referenced_media,
            dry_run=False,
        )
        import_job.status = JobStatus.COMPLETE
        delete_unused_media(import_job)
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

    missing_uploaded_media = get_missing_uploaded_media(data, import_job)
    missing_referenced_media_ids = get_missing_referenced_media(
        data, import_job.site.id
    )

    try:
        process_import_job_data(
            data,
            import_job,
            missing_uploaded_media,
            missing_referenced_media_ids,
            dry_run=True,
        )
        import_job.validation_status = JobStatus.COMPLETE
    except Exception as e:
        logger.error(e)
        import_job.validation_status = JobStatus.FAILED
    finally:
        import_job.save()


def get_associated_filenames(import_job):
    """
    Get a list of filenames for the uploaded files associated with the import-job.
    """
    associated_audio_files = list(
        File.objects.filter(import_job=import_job).values_list("content", flat=True)
    )
    associated_video_files = list(
        VideoFile.objects.filter(import_job=import_job).values_list(
            "content", flat=True
        )
    )
    associated_image_files = list(
        ImageFile.objects.filter(import_job=import_job).values_list(
            "content", flat=True
        )
    )
    associated_files = (
        associated_image_files + associated_video_files + associated_audio_files
    )

    return [file.split("/")[-1] for file in associated_files]


def get_missing_uploaded_media(data, import_job):
    """
    Checks for missing media files in the specified import-job by comparing file names present in the data
    with the uploaded files associated with the import-job.
    Returns a list of missing media files.
    """

    associated_filenames = get_associated_filenames(import_job)
    missing_media = []
    media_fields = [
        "AUDIO_FILENAME",
        "AUDIO_2_FILENAME",
        "AUDIO_3_FILENAME",
        "AUDIO_4_FILENAME",
        "AUDIO_5_FILENAME",
        "IMG_FILENAME",
        "IMG_2_FILENAME",
        "IMG_3_FILENAME",
        "IMG_4_FILENAME",
        "IMG_5_FILENAME",
        "VIDEO_FILENAME",
        "VIDEO_2_FILENAME",
        "VIDEO_3_FILENAME",
        "VIDEO_4_FILENAME",
        "VIDEO_5_FILENAME",
    ]

    for field in media_fields:
        field = field.lower()
        data.headers = [h.lower() for h in data.headers]
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
                missing_media.append(
                    {"idx": idx + 1, "filename": filename, "column": field}
                )

    return missing_media


def get_missing_referenced_media(data, site_id):
    """
    Checks the media files referenced by ID in the csv data file and returns errors for any that do not exist or are not
    from an accessible site (same site or one with shared media)
    """

    return (
        AudioImporter.get_missing_referenced_media(site_id, data)
        + ImageImporter.get_missing_referenced_media(site_id, data)
        + VideoImporter.get_missing_referenced_media(site_id, data)
    )


def get_missing_referenced_entries(data, site_id):
    """
    Checks the dictionary entries referenced by ID in the csv data file and returns errors for any that do not exist.
    """

    return DictionaryEntryImporter.get_missing_referenced_entries(site_id, data)


def delete_unused_media(import_job):
    """
    Checks for, and deletes, any media files that were uploaded for the import job but not associated with a media model
    i.e. Not used in the import.
    """
    logger = get_task_logger(__name__)

    try:
        ImageFile.objects.filter(
            import_job_id=import_job.id, image__isnull=True
        ).delete()
        VideoFile.objects.filter(
            import_job_id=import_job.id, video__isnull=True
        ).delete()
        File.objects.filter(import_job_id=import_job.id, audio__isnull=True).delete()
    except Exception as e:
        logger.warning(
            f"An exception occurred while trying to delete unused media files. Error: {e}"
        )


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
