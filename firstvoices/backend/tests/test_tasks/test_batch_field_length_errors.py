import pytest
import tablib
from django.core.files.uploadedfile import SimpleUploadedFile

from backend.models.constants import (
    DEFAULT_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_NOTE_LENGTH,
    Visibility,
)
from backend.models.import_jobs import ImportJob
from backend.models.jobs import JobStatus
from backend.models.update_jobs import UpdateJob
from backend.tasks.import_job_tasks import validate_import_job
from backend.tasks.update_job_tasks import validate_update_job
from backend.tests import factories
from backend.tests.utils import get_sample_file

MEDIA_TITLE_LENGTH = 200  # MediaBase.title max_length

MEDIA_FILES = {
    "audio": (factories.FileFactory, "sample-audio.mp3", "audio/mpeg"),
    "document": (factories.FileFactory, "sample-document.pdf", "application/pdf"),
    "img": (factories.ImageFileFactory, "sample-image.jpg", "image/jpeg"),
    "video": (factories.VideoFileFactory, "video_example_small.mp4", "video/mp4"),
}


def get_length_error(max_length):
    return f"Ensure this value has at most {max_length} characters (it has {max_length + 1})."


class BaseBatchFieldLengthErrorsTest:
    """
    Field length error messages for batch jobs. Each test uses one row at the max length (valid)
    and one row over the max length (error)
    """

    TASK = None
    JOB_MODEL = None
    JOB_FACTORY = None
    JOB_RELATION_FIELD = None
    SUCCESS_COUNT_FIELD = None

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def add_entry_ids(self, headers, rows):
        return headers, rows

    def get_job(self, headers, rows):
        headers, rows = self.add_entry_ids(headers, rows)
        data = tablib.Dataset(*rows, headers=headers)
        csv_file = SimpleUploadedFile(
            "field_length.csv", data.export("csv").encode("utf-8"), "text/csv"
        )

        return self.JOB_FACTORY(
            site=self.site,
            run_as_user=self.user,
            data=factories.FileFactory(content=csv_file),
            validation_status=JobStatus.ACCEPTED,
        )

    def add_media_file(self, job, prefix, filename):
        file_factory, sample_filename, mimetype = MEDIA_FILES[prefix]
        file_factory(
            site=self.site,
            content=get_sample_file(sample_filename, mimetype, title=filename),
            **{self.JOB_RELATION_FIELD: job},
        )

    def validate_job(self, job):
        self.TASK(job.id)
        return self.JOB_MODEL.objects.get(id=job.id)

    def assert_one_error_row(self, report, success_count):
        assert report.error_rows == 1
        assert getattr(report, self.SUCCESS_COUNT_FIELD) == success_count

    def test_entry_title_length_error(self):
        headers = ["title", "type"]
        rows = [
            ["a" * DEFAULT_TITLE_LENGTH, "word"],
            ["b" * (DEFAULT_TITLE_LENGTH + 1), "word"],
        ]
        job = self.validate_job(self.get_job(headers, rows))
        report = job.validation_report

        self.assert_one_error_row(report, success_count=1)
        error_row = report.rows.get(row_number=2)
        assert f"title: {get_length_error(DEFAULT_TITLE_LENGTH)}" in error_row.errors

    @pytest.mark.parametrize(
        "column, attribute, max_length",
        [
            ("translation", "translations", DEFAULT_TITLE_LENGTH),
            ("acknowledgement", "acknowledgements", MAX_NOTE_LENGTH),
            ("note", "notes", MAX_NOTE_LENGTH),
            ("alternate_spelling", "alternate_spellings", DEFAULT_TITLE_LENGTH),
            ("pronunciation", "pronunciations", DEFAULT_TITLE_LENGTH),
        ],
    )
    def test_entry_text_list_length_error(self, column, attribute, max_length):
        headers = ["title", "type", column]
        rows = [
            ["valid_entry", "word", "a" * max_length],
            ["invalid_entry", "word", "a" * (max_length + 1)],
        ]
        job = self.validate_job(self.get_job(headers, rows))
        report = job.validation_report

        self.assert_one_error_row(report, success_count=1)
        error_row = report.rows.get(row_number=2)
        expected_error_message = (
            f"{attribute}: Item 1 in the array did not validate: "
            f"{get_length_error(max_length)}"
        )
        assert expected_error_message in error_row.errors

    def test_entry_text_list_numbered_column_length_error(self):
        # the item number in the message matches the position of the value, e.g. translation_2
        headers = ["title", "type", "translation", "translation_2"]
        rows = [
            ["valid_entry", "word", "first", "a" * DEFAULT_TITLE_LENGTH],
            ["invalid_entry", "word", "first", "a" * (DEFAULT_TITLE_LENGTH + 1)],
        ]
        job = self.validate_job(self.get_job(headers, rows))
        report = job.validation_report

        self.assert_one_error_row(report, success_count=1)
        error_row = report.rows.get(row_number=2)
        expected_error_message = (
            "translations: Item 2 in the array did not validate: "
            f"{get_length_error(DEFAULT_TITLE_LENGTH)}"
        )
        assert expected_error_message in error_row.errors

    @pytest.mark.parametrize("prefix", ["audio", "document", "img", "video"])
    @pytest.mark.parametrize(
        "field, max_length",
        [
            ("title", MEDIA_TITLE_LENGTH),
            ("description", MAX_DESCRIPTION_LENGTH),
        ],
    )
    def test_media_field_length_error(self, prefix, field, max_length):
        extension = MEDIA_FILES[prefix][1].split(".")[-1]
        valid_filename = f"max_length_{prefix}.{extension}"
        invalid_filename = f"over_length_{prefix}.{extension}"

        headers = ["title", "type", f"{prefix}_filename", f"{prefix}_{field}"]
        rows = [
            ["valid_entry", "word", valid_filename, "a" * max_length],
            ["invalid_entry", "word", invalid_filename, "a" * (max_length + 1)],
        ]
        job = self.get_job(headers, rows)
        self.add_media_file(job, prefix, valid_filename)
        self.add_media_file(job, prefix, invalid_filename)

        job = self.validate_job(job)
        report = job.validation_report

        self.assert_one_error_row(report, success_count=2)
        error_row = report.rows.get(row_number=2)
        assert f"{field}: {get_length_error(max_length)}" in error_row.errors


@pytest.mark.django_db
class TestImportJobFieldLengthErrors(BaseBatchFieldLengthErrorsTest):
    TASK = validate_import_job
    JOB_MODEL = ImportJob
    JOB_FACTORY = factories.ImportJobFactory
    JOB_RELATION_FIELD = "import_job"
    SUCCESS_COUNT_FIELD = "new_rows"


@pytest.mark.django_db
class TestUpdateJobFieldLengthErrors(BaseBatchFieldLengthErrorsTest):
    TASK = validate_update_job
    JOB_MODEL = UpdateJob
    JOB_FACTORY = factories.UpdateJobFactory
    JOB_RELATION_FIELD = "update_job"
    SUCCESS_COUNT_FIELD = "updated_rows"

    def add_entry_ids(self, headers, rows):
        # update jobs need an existing entry for each row
        entry_ids = [
            str(factories.DictionaryEntryFactory.create(site=self.site).id)
            for _ in rows
        ]
        return ["id"] + headers, [
            [entry_id] + row for entry_id, row in zip(entry_ids, rows)
        ]
