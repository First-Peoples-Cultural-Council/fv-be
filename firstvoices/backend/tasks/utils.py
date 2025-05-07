import io
import sys

import tablib
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from backend.models.files import File
from backend.models.import_jobs import (
    ImportJob,
    ImportJobReportRow,
    JobStatus,
    RowStatus,
)

ASYNC_TASK_START_TEMPLATE = "Task started. Additional info: %s."
ASYNC_TASK_END_TEMPLATE = "Task ended."

VALID_HEADERS = [
    "id",
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
    in_memory_csv_file = io.BytesIO(failed_row_export.encode("utf-8-sig"))
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
        error_row.errors += errors
        error_row.save()


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
