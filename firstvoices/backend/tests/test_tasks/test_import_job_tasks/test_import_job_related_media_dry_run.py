import pytest

from backend.models import ImportJob
from backend.models.constants import Visibility
from backend.models.files import File
from backend.models.import_jobs import JobStatus
from backend.tasks.import_job_tasks import validate_import_job
from backend.tests import factories
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestImportJobRelatedMediaDryRun:
    MIMETYPE = "text/csv"
    CSV_FILES_DIR = "test_tasks/test_import_job_tasks/resources"
    MEDIA_FILES_DIR = "test_tasks/test_import_job_tasks/resources/related_media"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def test_related_media_columns_accepted(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_columns_accepted.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert "audio_ids" in validation_report.accepted_columns
        assert "audio_filename" in validation_report.accepted_columns
        assert "document_ids" in validation_report.accepted_columns
        assert "document_filename" in validation_report.accepted_columns
        assert "img_ids" in validation_report.accepted_columns
        assert "img_filename" in validation_report.accepted_columns
        assert "video_ids" in validation_report.accepted_columns
        assert "video_filename" in validation_report.accepted_columns

    def test_missing_media(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_missing_media.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        assert import_job.validation_report.error_rows == 4

        error_rows = import_job.validation_report.rows.all().order_by("row_number")
        error_rows_numbers = error_rows.values_list("row_number", flat=True)

        assert list(error_rows_numbers) == [1, 2, 3, 4]

        assert (
            "Media file missing in uploaded files: sample_audio.mp3, column: audio_filename."
            in error_rows[0].errors
        )
        assert (
            "Media file missing in uploaded files: sample_image.jpg, column: img_filename."
            in error_rows[1].errors
        )
        assert (
            "Media file missing in uploaded files: sample_video.mp4, column: video_filename."
            in error_rows[2].errors
        )
        assert (
            "Media file missing in uploaded files: sample_document.pdf, column: document_filename."
            in error_rows[3].errors
        )

    def test_missing_media_multiple(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_missing_media_multiple.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        # Adding the media to the db
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_missing_media_multiple.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_missing_media_multiple.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_missing_media_multiple.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_missing_media_multiple.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )

        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 4

        error_rows = validation_report.rows.all().order_by("row_number")
        assert (
            "Media file missing in uploaded files: missing_audio.mp3, column: audio_2_filename."
            in error_rows[0].errors
        )
        assert (
            "Media file missing in uploaded files: missing_image.jpg, column: img_2_filename."
            in error_rows[1].errors
        )
        assert (
            "Media file missing in uploaded files: missing_video.mp4, column: video_2_filename."
            in error_rows[2].errors
        )
        assert (
            "Media file missing in uploaded files: missing_document.pdf, column: document_2_filename."
            in error_rows[3].errors
        )

    def test_all_media_present(self):
        # Start with a validated import job that has missing media
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_all_media_present.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        assert import_job.validation_report.error_rows == 4

        # Adding the media to the db
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_all_media_present.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_all_media_present.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_all_media_present.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_all_media_present.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )

        # Validating again
        import_job.validation_status = JobStatus.ACCEPTED
        import_job.save()
        validate_import_job(import_job.id)

        # Verifying all missing media errors are resolved now
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0
        assert validation_report.rows.count() == 0

    def test_related_media_duplicate_ids(self):
        audio = factories.AudioFactory.create(
            id="869a8617-6285-49b2-ada2-96b4f9145451", site=self.site
        )
        factories.ImageFactory.create(
            id="271e4aa1-e7ed-4e6c-8e31-e3f28f68b50e", site=self.site
        )
        factories.VideoFactory.create(
            id="5b79d515-41ff-4404-beb2-acec6ec91a57", site=self.site
        )
        factories.DocumentFactory.create(
            id="23dd1f83-be6b-42b7-9aa8-2310601f5497", site=self.site
        )

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_duplicate_ids.csv",
            mimetype=self.MIMETYPE,
        )

        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=audio.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0
        assert validation_report.new_rows == 5

    def test_related_media_duplicate_filenames(self):
        # If multiple rows have same filenames, only the first media instance will be imported
        # and used. The rest of the media will not be imported and should not give any issues.
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_duplicate_filenames.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        # Adding the media to the db
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_duplicate_filenames.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_duplicate_filenames.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_duplicate_filenames.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_duplicate_filenames.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )

        factories.PersonFactory.create(
            name="test_related_media_duplicate_filenames_speaker_1", site=self.site
        )
        factories.PersonFactory.create(
            name="test_related_media_duplicate_filenames_speaker_2", site=self.site
        )

        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0

    def test_related_audio_speakers(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_audio_speakers.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)

        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_audio_speakers.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_audio_speakers_2.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 1
        assert (
            "No Person found with the provided name in column audio_speaker."
            in validation_report.rows.all()[0].errors
        )

        factories.PersonFactory.create(
            name="test_related_audio_speakers_speaker_1", site=self.site
        )
        factories.PersonFactory.create(
            name="test_related_audio_speakers_speaker_2", site=self.site
        )

        import_job.validation_status = JobStatus.ACCEPTED
        import_job.save()
        validate_import_job(import_job.id)
        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0

    def test_related_media_id_does_not_exist(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_id_does_not_exist.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 5

    def test_failed_rows_csv_deleted_and_replaced(self):
        # Start with a validated import job that has missing media
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_failed_rows_csv_deleted_and_replaced.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        # Refreshed instance
        import_job = ImportJob.objects.get(id=import_job.id)
        first_failed_rows_csv_id = import_job.failed_rows_csv.id

        # Add some of the media to the db, not all files
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_failed_rows_csv_deleted_and_replaced.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_failed_rows_csv_deleted_and_replaced.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_failed_rows_csv_deleted_and_replaced.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )

        # Validating again
        import_job.validation_status = JobStatus.ACCEPTED
        import_job.save()
        validate_import_job(import_job.id)

        revalidated_import_job = ImportJob.objects.get(id=import_job.id)

        # Check that the out of date csv has been deleted
        first_failed_rows_csv = File.objects.filter(
            site=self.site, id=first_failed_rows_csv_id
        )
        assert len(first_failed_rows_csv) == 0

        # Confirm there is a new csv
        assert first_failed_rows_csv_id != revalidated_import_job.failed_rows_csv.id
        assert revalidated_import_job.failed_rows_csv is not None
        validation_report = revalidated_import_job.validation_report
        assert validation_report.error_rows == 1

    def test_multiple_errors_in_single_row(self):
        # If there are multiple issues present in one row, all issues should be displayed
        # along with their column name

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_multiple_errors_in_single_row.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        # Add media to db
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_multiple_errors_in_single_row.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_multiple_errors_in_single_row.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_multiple_errors_in_single_row.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_multiple_errors_in_single_row.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )

        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 1

        error_row = validation_report.rows.get(row_number=1)
        assert len(error_row.errors) == 4
        assert (
            "Invalid value in include_in_games column. Expected 'true' or 'false'."
            in error_row.errors
        )
        assert (
            "No Person found with the provided name in column audio_speaker."
            in error_row.errors
        )
        assert (
            "Invalid value in img_include_in_kids_site column. Expected 'true' or 'false'."
            in error_row.errors
        )
        assert (
            "Invalid value in video_include_in_kids_site column. Expected 'true' or 'false'."
            in error_row.errors
        )

    def test_related_media_id_wrong_type(self):
        # Adding media files but mixing their types,
        # e.g. using an image id in the video field and so on
        factories.AudioFactory.create(
            site=self.site, id="51edee56-f81b-4fa4-8f2b-ed1e5cda75d0"
        )
        factories.ImageFactory.create(
            site=self.site, id="79642798-23f5-49bb-8f38-b6502419981b"
        )
        factories.VideoFactory.create(
            site=self.site, id="59d9b20c-a0d9-43bf-8940-b714f185c40d"
        )
        factories.DocumentFactory.create(
            site=self.site, id="84d7f036-ac6e-4066-a259-881f1499d756"
        )

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_id_wrong_type.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 5

    def test_related_media_id_shared_site(self):
        audio = factories.AudioFactory.create(id="f5174282-0fa9-4639-864a-2d0701b0efe0")
        factories.SiteFeatureFactory.create(
            site=audio.site, key="shared_media", is_enabled=True
        )

        document = factories.DocumentFactory.create(
            id="0097c7c1-ad46-498f-9613-eb1c2a4219cc"
        )
        factories.SiteFeatureFactory.create(
            site=document.site, key="SHARED_MEDIA", is_enabled=True
        )

        image = factories.ImageFactory.create(id="7d6908ef-5774-4ff1-a410-9cdb984414f5")
        factories.SiteFeatureFactory.create(
            site=image.site, key="shared_media", is_enabled=True
        )

        video = factories.VideoFactory.create(id="d920792c-41de-4049-8212-c4c6d0a05620")
        factories.SiteFeatureFactory.create(
            site=video.site, key="SHARED_MEDIA", is_enabled=True
        )

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_id_shared_site.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )
        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report
        assert validation_report.error_rows == 0
        assert validation_report.new_rows == 5

    def test_invalid_video_embed_links(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_invalid_video_embed_links.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.ACCEPTED,
        )

        validate_import_job(import_job.id)

        import_job = ImportJob.objects.get(id=import_job.id)
        validation_report = import_job.validation_report

        assert validation_report.new_rows == 0
        assert validation_report.error_rows == 3

        error_rows = validation_report.rows.all().order_by("row_number")
        assert (
            "related_video_links: Item 1 in the array did not validate: Enter a valid URL."
            in error_rows[0].errors
        )
        assert (
            "related_video_links: Duplicate urls found in list." in error_rows[1].errors
        )
        assert (
            "related_video_links: Duplicate urls found in list." in error_rows[2].errors
        )
