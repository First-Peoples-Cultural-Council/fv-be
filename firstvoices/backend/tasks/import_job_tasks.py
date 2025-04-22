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
from backend.models.media import ImageFile, VideoFile
from backend.resources.dictionary import DictionaryEntryResource
from backend.resources.media import AudioResource, ImageResource, VideoResource
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
    "audio_acknowledgement",
    "audio_include_in_kids_site",
    "audio_include_in_games",
    "audio_speaker",
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


def separate_data(data):
    """
    Splits the cleaned CSV data into two separate datasets, one to be used for dictionary entry resource,
    and one for audio resource.
    """
    audio_preset_columns = [
        "audio_filename",
        "audio_title",
        "audio_description",
        "audio_speaker",
        "audio_speaker_2",
        "audio_speaker_3",
        "audio_speaker_4",
        "audio_speaker_5",
        "audio_acknowledgement",
        "audio_include_in_kids_site",
        "audio_include_in_games",
    ]

    img_preset_columns = [
        "img_filename",
        "img_title",
        "img_description",
        "img_acknowledgement",
        "img_include_in_kids_site",
    ]

    video_preset_columns = [
        "video_filename",
        "video_title",
        "video_description",
        "video_acknowledgement",
        "video_include_in_kids_site",
    ]

    audio_columns = [col for col in audio_preset_columns if col in data.headers]
    img_columns = [col for col in img_preset_columns if col in data.headers]
    video_columns = [col for col in video_preset_columns if col in data.headers]

    audio_data = tablib.Dataset(headers=audio_columns)
    img_data = tablib.Dataset(headers=img_columns)
    video_data = tablib.Dataset(headers=video_columns)

    dictionary_entries_data = tablib.Dataset(
        headers=[
            col
            for col in data.headers
            if col not in (audio_columns + img_columns + video_columns)
            or col in ["audio_filename", "img_filename", "video_filename"]
        ]
    )

    # Audio data
    if "audio_filename" in data.headers:
        for row in data.dict:
            audio_row = [row[col] for col in audio_columns if col in data.headers]
            audio_data.append(audio_row)

    filtered_audio_data = tablib.Dataset(headers=audio_data.headers)
    for row in audio_data.dict:
        if row.get("audio_filename") not in ["", None]:
            filtered_audio_data.append([row.get(col) for col in audio_data.headers])

    # Image data
    if "img_filename" in data.headers:
        for row in data.dict:
            img_row = [row[col] for col in img_columns if col in data.headers]
            img_data.append(img_row)

    filtered_img_data = tablib.Dataset(headers=img_data.headers)
    for row in img_data.dict:
        if row.get("img_filename") not in ["", None]:
            filtered_img_data.append([row.get(col) for col in img_data.headers])

    # Video data
    if "video_filename" in data.headers:
        for row in data.dict:
            video_row = [row[col] for col in video_columns if col in data.headers]
            video_data.append(video_row)

    filtered_video_data = tablib.Dataset(headers=video_data.headers)
    for row in video_data.dict:
        if row.get("video_filename") not in ["", None]:
            filtered_video_data.append([row.get(col) for col in video_data.headers])

    for row in data.dict:
        dictionary_entries_row = [
            row[col]
            for col in data.headers
            if col not in (audio_columns + img_columns + video_columns)
            or col in ["audio_filename", "img_filename", "video_filename"]
        ]
        dictionary_entries_data.append(dictionary_entries_row)

    return (
        dictionary_entries_data,
        filtered_audio_data,
        filtered_img_data,
        filtered_video_data,
    )


def import_audio_resource(import_job, audio_data, dictionary_entry_data, dry_run):
    """
    Imports audio files and appends IDs of the imported files as related_audio in dictionary_entry_data.
    Returns updated dictionary_entry_data and result from audio import.
    """

    audio_import_result = AudioResource(
        site=import_job.site,
        run_as_user=import_job.run_as_user,
        import_job=import_job.id,
    ).import_data(dataset=audio_data, dry_run=dry_run)

    # Adding audio ids
    if audio_import_result.totals["new"]:
        audio_lookup = {
            row["audio_filename"]: row["id"]
            for row in audio_data.dict
            if row.get("audio_filename")
        }
        dictionary_entry_data.append_col(
            [""] * len(dictionary_entry_data), header="related_audio"
        )
        related_audio_col_index = dictionary_entry_data.headers.index("related_audio")
        for i, row in enumerate(dictionary_entry_data.dict):
            audio_filename = row.get("audio_filename")
            related_id = audio_lookup.get(audio_filename, "")
            row_list = list(dictionary_entry_data[i])
            row_list[related_audio_col_index] = related_id  # comma separated string
            dictionary_entry_data[i] = tuple(row_list)

    return audio_import_result, dictionary_entry_data


def import_img_resource(import_job, img_data, dictionary_entry_data, dry_run):
    """
    Imports image files and appends IDs of the imported files as related_images in dictionary_entry_data.
    Returns updated dictionary_entry_data and result from image import.
    """

    img_import_result = ImageResource(
        site=import_job.site,
        run_as_user=import_job.run_as_user,
        import_job=import_job.id,
    ).import_data(dataset=img_data, dry_run=dry_run)

    # Adding image ids
    if img_import_result.totals["new"]:
        img_lookup = {
            row["img_filename"]: row["id"]
            for row in img_data.dict
            if row.get("img_filename")
        }
        dictionary_entry_data.append_col(
            [""] * len(dictionary_entry_data), header="related_images"
        )
        related_img_col_index = dictionary_entry_data.headers.index("related_images")
        for i, row in enumerate(dictionary_entry_data.dict):
            img_filename = row.get("img_filename")
            related_id = img_lookup.get(img_filename, "")
            row_list = list(dictionary_entry_data[i])
            row_list[related_img_col_index] = related_id  # comma separated string
            dictionary_entry_data[i] = tuple(row_list)

    return img_import_result, dictionary_entry_data


def import_video_resource(import_job, video_data, dictionary_entry_data, dry_run):
    """
    Imports video files and appends IDs of the imported files as related_videos in dictionary_entry_data.
    Returns updated dictionary_entry_data and result from video import.
    """

    video_import_result = VideoResource(
        site=import_job.site,
        run_as_user=import_job.run_as_user,
        import_job=import_job.id,
    ).import_data(dataset=video_data, dry_run=dry_run)

    # Adding image ids
    if video_import_result.totals["new"]:
        video_lookup = {
            row["video_filename"]: row["id"]
            for row in video_data.dict
            if row.get("video_filename")
        }
        dictionary_entry_data.append_col(
            [""] * len(dictionary_entry_data), header="related_videos"
        )
        related_video_col_index = dictionary_entry_data.headers.index("related_videos")
        for i, row in enumerate(dictionary_entry_data.dict):
            video_filename = row.get("video_filename")
            related_id = video_lookup.get(video_filename, "")
            row_list = list(dictionary_entry_data[i])
            row_list[related_video_col_index] = related_id  # comma separated string
            dictionary_entry_data[i] = tuple(row_list)

    return video_import_result, dictionary_entry_data


def import_dictionary_entry_resource(import_job, dictionary_entry_data, dry_run):
    """
    Imports dictionary entries and returns the import result.
    """
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

    # If the row already exists, add message to the errors list.
    existing_error_rows = ImportJobReportRow.objects.filter(report=report).values_list(
        "row_number", flat=True
    )
    for row in audio_import_result.rows:
        if row.import_type == RowResult.IMPORT_TYPE_SKIP:
            if row.number in existing_error_rows:
                error_row_instance = ImportJobReportRow.objects.get(
                    report=report, row_number=row.number
                )
                error_row_instance.errors = (
                    error_row_instance.errors + row.error_messages
                )
            else:
                error_row_instance = ImportJobReportRow(
                    site=import_job.site,
                    report=report,
                    status=RowStatus.ERROR,
                    row_number=row.number,
                    errors=row.error_messages,
                )
            error_row_instance.save()

    # If the row already exists, add message to the errors list.
    existing_error_rows = ImportJobReportRow.objects.filter(report=report).values_list(
        "row_number", flat=True
    )
    for row in img_import_result.rows:
        if row.import_type == RowResult.IMPORT_TYPE_SKIP:
            if row.number in existing_error_rows:
                error_row_instance = ImportJobReportRow.objects.get(
                    report=report, row_number=row.number
                )
                error_row_instance.errors = (
                    error_row_instance.errors + row.error_messages
                )
            else:
                error_row_instance = ImportJobReportRow(
                    site=import_job.site,
                    report=report,
                    status=RowStatus.ERROR,
                    row_number=row.number,
                    errors=row.error_messages,
                )
            error_row_instance.save()

    # If the row already exists, add message to the errors list.
    existing_error_rows = ImportJobReportRow.objects.filter(report=report).values_list(
        "row_number", flat=True
    )
    for row in video_import_result.rows:
        if row.import_type == RowResult.IMPORT_TYPE_SKIP:
            if row.number in existing_error_rows:
                error_row_instance = ImportJobReportRow.objects.get(
                    report=report, row_number=row.number
                )
                error_row_instance.errors = (
                    error_row_instance.errors + row.error_messages
                )
            else:
                error_row_instance = ImportJobReportRow(
                    site=import_job.site,
                    report=report,
                    status=RowStatus.ERROR,
                    row_number=row.number,
                    errors=row.error_messages,
                )
            error_row_instance.save()

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
    dictionary_entry_data, audio_data, img_data, video_data = separate_data(
        cleaned_data
    )

    audio_import_result, dictionary_entry_data = import_audio_resource(
        import_job, audio_data, dictionary_entry_data, dry_run
    )
    img_import_result, dictionary_entry_data = import_img_resource(
        import_job, img_data, dictionary_entry_data, dry_run
    )
    video_import_result, dictionary_entry_data = import_video_resource(
        import_job, video_data, dictionary_entry_data, dry_run
    )
    dictionary_entry_import_result = import_dictionary_entry_resource(
        import_job, dictionary_entry_data, dry_run
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
    media_filename_list = ["AUDIO_FILENAME", "IMG_FILENAME", "VIDEO_FILENAME"]
    for media_filename in media_filename_list:
        if media_filename in data.headers:
            for idx, filename in enumerate(data[media_filename]):
                if filename and filename not in associated_filenames:
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
