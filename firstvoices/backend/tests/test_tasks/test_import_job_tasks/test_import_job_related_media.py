import pytest

from backend.models import DictionaryEntry
from backend.models.constants import Visibility
from backend.models.import_jobs import JobStatus
from backend.tasks.import_job_tasks import confirm_import_job
from backend.tests import factories
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestImportJobRelatedMedia:
    MIMETYPE = "text/csv"
    CSV_FILES_DIR = "test_tasks/test_import_job_tasks/resources"
    MEDIA_FILES_DIR = "test_tasks/test_import_job_tasks/resources/related_media"

    def setup_method(self):
        self.user = factories.factories.get_superadmin()
        self.site = factories.SiteFactory(visibility=Visibility.PUBLIC)

    def test_related_audio(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_audio.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        # Adding media
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_audio_file_1.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_audio_file_2.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )

        # Adding speakers
        factories.PersonFactory.create(
            name="test_related_audio_file_1_speaker_1", site=self.site
        )
        factories.PersonFactory.create(
            name="test_related_audio_file_1_speaker_2", site=self.site
        )
        factories.PersonFactory.create(
            name="test_related_audio_file_2_speaker_1", site=self.site
        )
        factories.PersonFactory.create(
            name="test_related_audio_file_2_speaker_2", site=self.site
        )

        confirm_import_job(import_job.id)

        entry = DictionaryEntry.objects.get(title="test_related_audio_word_1")

        # Verifying metadata for related audio 1
        related_audio_1 = entry.related_audio.get(
            title="test_related_audio_file_1_title"
        )
        related_audio_1_speakers = list(
            related_audio_1.speakers.all().values_list("name", flat=True)
        )
        assert "test_related_audio_file_1_speaker_1" in related_audio_1_speakers
        assert "test_related_audio_file_1_speaker_2" in related_audio_1_speakers
        assert "test_related_audio_file_1.mp3" in related_audio_1.original.content.name
        assert related_audio_1.title == "test_related_audio_file_1_title"
        assert related_audio_1.description == "test_related_audio_file_1_desc"
        assert related_audio_1.acknowledgement == "test_related_audio_file_1_ack"
        assert related_audio_1.exclude_from_games is True
        assert related_audio_1.exclude_from_kids is False
        assert related_audio_1.system_last_modified >= related_audio_1.last_modified
        assert related_audio_1.system_last_modified_by == import_job.created_by

        # Verifying metadata for related audio 2
        related_audio_2 = entry.related_audio.get(
            title="test_related_audio_file_2_title"
        )
        related_audio_2_speakers = list(
            related_audio_2.speakers.all().values_list("name", flat=True)
        )
        assert "test_related_audio_file_2_speaker_1" in related_audio_2_speakers
        assert "test_related_audio_file_2_speaker_2" in related_audio_2_speakers
        assert "test_related_audio_file_2.mp3" in related_audio_2.original.content.name
        assert related_audio_2.title == "test_related_audio_file_2_title"
        assert related_audio_2.description == "test_related_audio_file_2_desc"
        assert related_audio_2.acknowledgement == "test_related_audio_file_2_ack"
        assert related_audio_2.exclude_from_games is True
        assert related_audio_2.exclude_from_kids is False
        assert related_audio_2.system_last_modified >= related_audio_2.last_modified
        assert related_audio_2.system_last_modified_by == import_job.created_by

    def test_related_documents(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_documents.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_documents_file_1.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_documents_file_2.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )

        confirm_import_job(import_job.id)

        entry = DictionaryEntry.objects.get(title="test_related_documents_word_1")

        # Verifying metadata for related doc 1
        related_document_1 = entry.related_documents.get(
            title="test_related_documents_file_1_title"
        )
        assert (
            "test_related_documents_file_1.pdf"
            in related_document_1.original.content.name
        )
        assert related_document_1.title == "test_related_documents_file_1_title"
        assert related_document_1.description == "test_related_documents_file_1_desc"
        assert related_document_1.acknowledgement == "test_related_documents_file_1_ack"
        assert related_document_1.exclude_from_games is False
        assert related_document_1.exclude_from_kids is False
        assert (
            related_document_1.system_last_modified >= related_document_1.last_modified
        )
        assert related_document_1.system_last_modified_by == import_job.created_by

        # Verifying metadata for related doc 2
        related_document_2 = entry.related_documents.get(
            title="test_related_documents_file_2_title"
        )
        assert (
            "test_related_documents_file_2.pdf"
            in related_document_2.original.content.name
        )
        assert related_document_2.title == "test_related_documents_file_2_title"
        assert related_document_2.description == "test_related_documents_file_2_desc"
        assert related_document_2.acknowledgement == "test_related_documents_file_2_ack"
        assert related_document_2.exclude_from_games is False
        assert related_document_2.exclude_from_kids is False
        assert (
            related_document_2.system_last_modified >= related_document_2.last_modified
        )
        assert related_document_2.system_last_modified_by == import_job.created_by

    def test_related_images(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_images.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_images_file_1.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_images_file_2.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )

        confirm_import_job(import_job.id)

        entry = DictionaryEntry.objects.get(title="test_related_images_word_1")

        # Verifying metadata for related image 1
        related_image_1 = entry.related_images.get(
            title="test_related_images_file_1_title"
        )
        assert "test_related_images_file_1.jpg" in related_image_1.original.content.name
        assert related_image_1.title == "test_related_images_file_1_title"
        assert related_image_1.description == "test_related_images_file_1_desc"
        assert related_image_1.acknowledgement == "test_related_images_file_1_ack"
        assert related_image_1.exclude_from_kids is False
        assert related_image_1.exclude_from_games is False
        assert related_image_1.system_last_modified >= related_image_1.last_modified
        assert related_image_1.system_last_modified_by == import_job.created_by

        # Verifying metadata for related image 2
        related_image_2 = entry.related_images.get(
            title="test_related_images_file_2_title"
        )
        assert "test_related_images_file_2.jpg" in related_image_2.original.content.name
        assert related_image_2.title == "test_related_images_file_2_title"
        assert related_image_2.description == "test_related_images_file_2_desc"
        assert related_image_2.acknowledgement == "test_related_images_file_2_ack"
        assert related_image_2.exclude_from_kids is False
        assert related_image_2.exclude_from_games is False
        assert related_image_2.system_last_modified >= related_image_2.last_modified
        assert related_image_2.system_last_modified_by == import_job.created_by

    def test_related_videos(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_videos.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            validation_status=JobStatus.COMPLETE,
            status=JobStatus.ACCEPTED,
        )

        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_videos_file_1.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_videos_file_2.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )
        confirm_import_job(import_job.id)

        entry = DictionaryEntry.objects.get(title="test_related_videos_word_1")

        # Verifying metadata for related video 1
        related_video_1 = entry.related_videos.get(
            title="test_related_videos_file_1_title"
        )
        assert "test_related_videos_file_1.mp4" in related_video_1.original.content.name
        assert related_video_1.title == "test_related_videos_file_1_title"
        assert related_video_1.description == "test_related_videos_file_1_desc"
        assert related_video_1.acknowledgement == "test_related_videos_file_1_ack"
        assert related_video_1.exclude_from_kids is False
        assert related_video_1.exclude_from_games is False
        assert related_video_1.system_last_modified >= related_video_1.last_modified
        assert related_video_1.system_last_modified_by == import_job.created_by

        # Verifying metadata for related video 2
        related_image_2 = entry.related_videos.get(
            title="test_related_videos_file_2_title"
        )
        assert "test_related_videos_file_2.mp4" in related_image_2.original.content.name
        assert related_image_2.title == "test_related_videos_file_2_title"
        assert related_image_2.description == "test_related_videos_file_2_desc"
        assert related_image_2.acknowledgement == "test_related_videos_file_2_ack"
        assert related_image_2.exclude_from_kids is False
        assert related_image_2.exclude_from_games is False
        assert related_image_2.system_last_modified >= related_image_2.last_modified
        assert related_image_2.system_last_modified_by == import_job.created_by
