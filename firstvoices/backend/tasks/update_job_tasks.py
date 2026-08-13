from copy import deepcopy

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
from backend.models import Alphabet, DictionaryEntry
from backend.models.import_jobs import ImportJob, ImportJobMode, ImportJobStatus
from backend.tasks.batch_utils import (
    create_or_append_error_row,
    get_missing_referenced_entries,
    get_missing_referenced_media,
    get_missing_uploaded_media,
    get_related_entry_headers,
    is_valid_header_variation,
    normalize_columns,
    verify_no_other_import_jobs_running,
)
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE
from backend.tasks.import_job_tasks import attach_csv_to_report, generate_report
from backend.utils.uuid_utils import is_valid_uuid


def get_valid_update_headers():
    importers = [
        AudioImporter,
        DocumentImporter,
        ImageImporter,
        VideoImporter,
        DictionaryEntryImporter,
    ]
    supported_columns = []
    for importer in importers:
        supported_columns += importer.get_supported_update_columns()
    return supported_columns


def clean_update_csv(data):

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

    # normalize title and related entry columns
    columns_to_normalize = ["title"] + get_related_entry_headers(cleaned_data)
    cleaned_data = normalize_columns(cleaned_data, columns_to_normalize)

    return accepted_headers, invalid_headers, cleaned_data


def add_unknown_character_warnings(cleaned_data, update_job, report):
    site = update_job.site
    if not Alphabet.objects.filter(site=site).exists():
        return
    alphabet = Alphabet.objects.get(site=site)
    warning_rows_count = 0

    # get a list of tuples of (row_number, title) for each row in the cleaned data
    data_titles = [
        (i + 1, row["title"])
        for i, row in enumerate(cleaned_data.dict)
        if row.get("title")
    ]

    # for each title in the cleaned data, check the custom order with the alphabet
    for row_number, title in data_titles:
        unknown_characters = alphabet.get_unknown_characters(title)
        if unknown_characters:
            warning_message = (
                f"WARNING: Title '{title}' contains unrecognized characters {unknown_characters} "
                f"that may affect sorting."
            )
            create_or_append_error_row(
                update_job, report, row_number, [warning_message]
            )
            warning_rows_count += 1

    if report.warnings is None:
        report.warnings = 0
    report.warnings += warning_rows_count
    report.save()
    return


def add_field_value_removal_warnings(cleaned_data, update_job, report):
    warning_rows_count = 0
    total_row_count = len(cleaned_data.dict)

    # for each nullable field, track the number of rows where the field is being removed
    nulled_field_counts = {
        "part_of_speech": 0,
        "category": 0,
        "translation": 0,
        "acknowledgement": 0,
        "note": 0,
        "alternate_spelling": 0,
        "pronunciation": 0,
        "related_entry_ids": 0,
        "audio_ids": 0,
        "document_ids": 0,
        "img_ids": 0,
        "video_ids": 0,
        "video_embed_links": 0,
        "external_system": 0,
        "external_system_entry_id": 0,
    }

    # for each row in cleaned data, process a set of fields cross-referencing with the existing data
    # to check if any fields are being removed
    for row in cleaned_data.dict:
        if (
            not is_valid_uuid(row["id"])
            or not DictionaryEntry.objects.filter(id=row["id"]).exists()
        ):
            continue
        else:
            entry = DictionaryEntry.objects.get(id=row["id"])

        # check entry text list fields:
        # part_of_speech', 'category', 'translation', 'acknowledgement', 'note', 'alternate_spelling', 'pronunciation'
        if (
            "part_of_speech" in row and not row.get("part_of_speech")
        ) and entry.part_of_speech:
            nulled_field_counts["part_of_speech"] += 1
        if (
            "category" in row and not row.get("category")
        ) and entry.categories.exists():
            nulled_field_counts["category"] += 1
        if ("translation" in row and not row.get("translation")) and entry.translations:
            nulled_field_counts["translation"] += 1
        if (
            "acknowledgement" in row and not row.get("acknowledgement")
        ) and entry.acknowledgements:
            nulled_field_counts["acknowledgement"] += 1
        if ("note" in row and not row.get("note")) and entry.notes:
            nulled_field_counts["note"] += 1
        if (
            "alternate_spelling" in row and not row.get("alternate_spelling")
        ) and entry.alternate_spellings:
            nulled_field_counts["alternate_spelling"] += 1
        if (
            "pronunciation" in row and not row.get("pronunciation")
        ) and entry.pronunciations:
            nulled_field_counts["pronunciation"] += 1

        # check related id/media fields:
        # 'related_entry_ids', 'audio_ids', 'document_ids', 'img_ids', 'video_ids', 'video_embed_links'
        if (
            "related_entry_ids" in row and not row.get("related_entry_ids")
        ) and entry.related_dictionary_entries.exists():
            nulled_field_counts["related_entry_ids"] += 1
        if (
            "audio_ids" in row and not row.get("audio_ids")
        ) and entry.related_audio.exists():
            nulled_field_counts["audio_ids"] += 1
        if (
            "document_ids" in row and not row.get("document_ids")
        ) and entry.related_documents.exists():
            nulled_field_counts["document_ids"] += 1
        if (
            "img_ids" in row and not row.get("img_ids")
        ) and entry.related_images.exists():
            nulled_field_counts["img_ids"] += 1
        if (
            "video_ids" in row and not row.get("video_ids")
        ) and entry.related_videos.exists():
            nulled_field_counts["video_ids"] += 1
        if (
            "video_embed_links" in row and not row.get("video_embed_links")
        ) and entry.related_video_links:
            nulled_field_counts["video_embed_links"] += 1

        # check external system fields: 'external_system', 'external_system_entry_id'
        if (
            "external_system" in row and not row.get("external_system")
        ) and entry.external_system:
            nulled_field_counts["external_system"] += 1
        if (
            "external_system_entry_id" in row
            and not row.get("external_system_entry_id")
        ) and entry.external_system_entry_id:
            nulled_field_counts["external_system_entry_id"] += 1

    for key, value in nulled_field_counts.items():
        # if any one field has been nulled in 30% or more of the rows, add a warning to the report
        if value / total_row_count >= 0.3:
            warning_message = (
                f"WARNING: The field '{key}' is being removed in {value} out of {total_row_count} rows "
                f"({value / total_row_count:.0%}). This may result in loss of data."
            )
            # a row number of -1 indicates that the errors are for the entire job, not a specific row
            create_or_append_error_row(update_job, report, -1, [warning_message])
            warning_rows_count += 1

    if report.warnings is None:
        report.warnings = 0
    report.warnings += warning_rows_count
    report.save()
    return


def process_update_job_data(
    data,
    update_job,
    missing_uploaded_media=[],
    missing_referenced_media=[],
    dry_run=True,
):
    """
    Primary method that cleans the CSV data, uses resources to update models, and generates a report.
    Used for both dry_run and actual imports.
    """
    missing_entries = get_missing_referenced_entries(data, update_job.site.id)

    accepted_headers, invalid_headers, cleaned_data = clean_update_csv(data)

    # import media first
    audio_import_results, audio_filename_map = AudioImporter.import_data(
        update_job, cleaned_data, dry_run
    )
    document_import_results, document_filename_map = DocumentImporter.import_data(
        update_job, cleaned_data, dry_run
    )
    img_import_results, img_filename_map = ImageImporter.import_data(
        update_job, cleaned_data, dry_run
    )
    video_import_results, video_filename_map = VideoImporter.import_data(
        update_job, cleaned_data, dry_run
    )

    # update dictionary entries
    dictionary_entry_update_result = DictionaryEntryImporter.update_data(
        update_job,
        cleaned_data,
        dry_run,
        missing_uploaded_media,
        missing_referenced_media,
        missing_entries,
        audio_filename_map,
        img_filename_map,
        video_filename_map,
        document_filename_map,
    )

    if dry_run:
        report = generate_report(
            import_job=update_job,
            accepted_columns=accepted_headers,
            ignored_columns=invalid_headers,
            audio_import_results=audio_import_results,
            document_import_results=document_import_results,
            img_import_results=img_import_results,
            video_import_results=video_import_results,
            dictionary_entry_import_result=dictionary_entry_update_result,
        )
        add_unknown_character_warnings(cleaned_data, update_job, report)
        add_field_value_removal_warnings(cleaned_data, update_job, report)
        attach_csv_to_report(data, update_job, report)


def run_update_job(data, update_job):
    """
    Executes the actual update operation (non dry-run mode) and updates the status attribute of the update job.
    """
    logger = get_task_logger(__name__)

    missing_uploaded_media = get_missing_uploaded_media(data, update_job)
    missing_referenced_media = get_missing_referenced_media(data, update_job.site.id)

    try:
        process_update_job_data(
            data,
            update_job,
            missing_uploaded_media,
            missing_referenced_media,
            dry_run=False,
        )
        update_job.status = ImportJobStatus.COMPLETE
    except Exception as e:
        logger.error(e)
        update_job.status = ImportJobStatus.FAILED
    finally:
        update_job.save()


def dry_run_update_job(data, update_job):
    """
    Performs a dry-run of the specified update job and updates the validation_status attribute of the update job.
    """
    logger = get_task_logger(__name__)

    missing_uploaded_media = get_missing_uploaded_media(data, update_job)
    missing_referenced_media_ids = get_missing_referenced_media(
        data, update_job.site.id
    )

    try:
        process_update_job_data(
            data,
            update_job,
            missing_uploaded_media,
            missing_referenced_media_ids,
            dry_run=True,
        )
        update_job.validation_status = ImportJobStatus.COMPLETE
    except Exception as e:
        logger.error(e)
        update_job.validation_status = ImportJobStatus.FAILED
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
    if update_job.validation_status != ImportJobStatus.ACCEPTED:
        logger.info("This job cannot be run due to consistency issues.")
        update_job.validation_status = ImportJobStatus.FAILED
        update_job.save()
        return

    if update_job.status in [
        ImportJobStatus.ACCEPTED,
        ImportJobStatus.STARTED,
        ImportJobStatus.COMPLETE,
    ]:
        logger.info(
            "This job could not be started as it is either queued, or already running or completed. "
            f"Update job id: {update_job_id}."
        )
        update_job.validation_status = ImportJobStatus.FAILED
        update_job.save()
        return

    verify_no_other_import_jobs_running(update_job)

    update_job.validation_status = ImportJobStatus.STARTED
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
    if update_job.status != ImportJobStatus.ACCEPTED:
        logger.info(
            f"This job cannot be run due to consistency issues. Update job id: {update_job_id}."
        )
        update_job.status = ImportJobStatus.FAILED
        update_job.save()
        return

    if update_job.validation_status != ImportJobStatus.COMPLETE:
        logger.info(
            f"Please validate the job before confirming the import. Update job id: {update_job_id}."
        )
        update_job.status = ImportJobStatus.FAILED
        update_job.save()
        return

    verify_no_other_import_jobs_running(update_job)

    update_job.status = ImportJobStatus.STARTED
    update_job.task_id = task_id

    run_update_job(data, update_job)
    update_job.save()

    logger.info(ASYNC_TASK_END_TEMPLATE)
