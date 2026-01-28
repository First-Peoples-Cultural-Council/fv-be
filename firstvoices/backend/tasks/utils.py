import io
import re
import sys

import tablib
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q
from django.utils.text import get_valid_filename
from rest_framework.exceptions import ValidationError

from backend.models.files import File
from backend.models.import_jobs import (
    ImportJob,
    ImportJobReportRow,
    JobStatus,
    RowStatus,
)
from backend.models.media import ImageFile, VideoFile
from backend.utils.character_utils import clean_input


def verify_no_other_import_jobs_running(current_job):
    # Method to verify that no other ImportJob tasks are running
    # on the provided site

    existing_incomplete_jobs = ImportJob.objects.filter(
        Q(site=current_job.site),
        Q(status__in=[JobStatus.ACCEPTED, JobStatus.STARTED])
        | Q(validation_status__in=[JobStatus.ACCEPTED, JobStatus.STARTED]),
    ).exclude(id=current_job.id)

    if len(existing_incomplete_jobs):
        raise ValidationError(
            "There is at least 1 job on this site that is already running or queued to run soon. "
            "Please wait for it to finish before starting a new one."
        )


def get_failed_rows_csv_file(import_job, data, error_row_numbers):
    # Generate a csv for the erroneous rows
    failed_row_dataset = []
    for row_num in error_row_numbers:
        failed_row_dataset.append(
            data[row_num - 1]
        )  # -1 to subtract to account for headers
    failed_row_dataset = tablib.Dataset(*failed_row_dataset)
    failed_row_dataset.headers = data.headers

    failed_row_export = failed_row_dataset.export("csv")
    in_memory_csv_file = io.BytesIO(failed_row_export.encode("utf-8-sig"))
    in_memory_csv_file = InMemoryUploadedFile(
        file=in_memory_csv_file,
        field_name="failed_rows_csv",
        name="failed_rows.csv",
        content_type="text/csv",
        size=sys.getsizeof(in_memory_csv_file),
        charset="utf-8",
    )
    # failed_row_csv_file does not need the import_job property to be set (that is for associated media)
    # The csv will be set to "failed_rows_csv" on import job in "attach_csv_to_report"
    failed_row_csv_file = File(
        content=in_memory_csv_file,
        site=import_job.site,
        created_by=import_job.last_modified_by,
        last_modified_by=import_job.last_modified_by,
    )
    failed_row_csv_file.save()
    return failed_row_csv_file


def create_or_append_error_row(import_job, report, row_number, errors):
    error_row, created = ImportJobReportRow.objects.get_or_create(
        site=import_job.site,
        report=report,
        row_number=row_number,
        defaults={
            "status": RowStatus.ERROR,
            "errors": errors,
        },
    )
    if not created:
        error_row.errors.extend(errors)
        error_row.save()


def is_valid_header_variation(input_header, all_headers, valid_headers):
    # If the header is a numeric variation (e.g., note_2), verify that it has a valid form and
    # the original header is also present (i.e., note)
    splits = re.match(r"^(.*?)(?:_([2-5]))?$", input_header)

    if not splits:
        return False

    lower_headers = [h.lower() for h in all_headers]

    prefix, number = splits.groups()

    prefix = prefix.lower()

    if prefix not in valid_headers:
        return False

    if number is None:
        return True

    if prefix not in lower_headers:
        return False

    return True


def get_related_entry_headers(import_data):
    related_entry_headers = [
        header
        for header in import_data.headers
        if header.lower().startswith("related_entry")
    ]
    if "related_entry_ids" in related_entry_headers:
        related_entry_headers.remove("related_entry_ids")

    return related_entry_headers


def normalize_columns(import_data, columns):
    # normalize data in specified columns using clean_input function
    normalized_data = tablib.Dataset(headers=import_data.headers)

    for row in import_data.dict:
        new_row = row.copy()
        for column in columns:
            if column in new_row:
                new_row[column] = clean_input(row[column])
        normalized_data.append([new_row[h] for h in import_data.headers])

    return normalized_data


def get_associated_filenames(import_job):
    """
    Get a list of filenames for the uploaded files associated with the import-job.
    """
    associated_audio_and_document_files = list(
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
        associated_image_files
        + associated_video_files
        + associated_audio_and_document_files
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
        "DOCUMENT_FILENAME",
        "DOCUMENT_2_FILENAME",
        "DOCUMENT_3_FILENAME",
        "DOCUMENT_4_FILENAME",
        "DOCUMENT_5_FILENAME",
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
