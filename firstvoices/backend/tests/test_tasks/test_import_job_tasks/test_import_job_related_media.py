from unittest.mock import MagicMock, patch

import pytest

from backend.models import DictionaryEntry
from backend.models.constants import Visibility
from backend.models.files import File
from backend.models.import_jobs import ImportJob, JobStatus
from backend.models.media import ImageFile, VideoFile
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

    def test_video_embed_links(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_video_embed_links.csv",
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

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 3

        entry_1 = DictionaryEntry.objects.get(title="test_video_embed_links_youtube")
        assert len(entry_1.related_video_links) == 1
        assert (
            entry_1.related_video_links[0]
            == "https://www.youtube.com/watch?v=N_Iyb0LkDUc"
        )

        entry_2 = DictionaryEntry.objects.get(title="test_video_embed_links_vimeo")
        assert len(entry_2.related_video_links) == 1
        assert entry_2.related_video_links[0] == "https://vimeo.com/226053498"

        entry_3 = DictionaryEntry.objects.get(title="test_video_embed_links_both")
        assert len(entry_3.related_video_links) == 2
        assert (
            "https://www.youtube.com/watch?v=N_Iyb0LkDUc" in entry_3.related_video_links
        )
        assert "https://vimeo.com/226053498" in entry_3.related_video_links

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

    def test_media_title_defaults_to_filename(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_media_title_defaults_to_filename.csv",
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
                filename="test_media_title_defaults_to_filename_audio.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_media_title_defaults_to_filename_doc.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_media_title_defaults_to_filename_image.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_media_title_defaults_to_filename_video.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )
        confirm_import_job(import_job.id)

        entry = DictionaryEntry.objects.get(
            title="test_media_title_defaults_to_filename_word_1"
        )

        related_audio = entry.related_audio.first()
        assert related_audio.title == "test_media_title_defaults_to_filename_audio.mp3"

        related_image = entry.related_images.first()
        assert related_image.title == "test_media_title_defaults_to_filename_image.jpg"

        related_video = entry.related_videos.first()
        assert related_video.title == "test_media_title_defaults_to_filename_video.mp4"

        related_document = entry.related_documents.first()
        assert related_document.title == "test_media_title_defaults_to_filename_doc.pdf"

    def test_duplicate_media_filenames(self):
        # If multiple rows have same filenames, only the first media instance will be imported
        # and used. The rest of the media will not be imported and should not give any issues.
        # All the latter entries will use the first imported media file.
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_duplicate_media_filenames.csv",
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
                filename="test_duplicate_media_filenames_audio.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_duplicate_media_filenames_doc.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_duplicate_media_filenames_image.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_duplicate_media_filenames_video.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )
        factories.PersonFactory.create(
            name="test_duplicate_media_filenames_speaker_1", site=self.site
        )
        factories.PersonFactory.create(
            name="test_duplicate_media_filenames_speaker_2", site=self.site
        )

        confirm_import_job(import_job.id)

        entry_1 = DictionaryEntry.objects.get(
            title="test_duplicate_media_filenames_word_1"
        )
        related_audio_entry_1 = entry_1.related_audio.first()
        related_document_entry_1 = entry_1.related_documents.first()
        related_image_entry_1 = entry_1.related_images.first()
        related_video_entry_1 = entry_1.related_videos.first()

        entry_2 = DictionaryEntry.objects.get(
            title="test_duplicate_media_filenames_phrase_1"
        )
        related_audio_entry_2 = entry_2.related_audio.first()
        related_document_entry_2 = entry_2.related_documents.first()
        related_image_entry_2 = entry_2.related_images.first()
        related_video_entry_2 = entry_2.related_videos.first()

        assert related_audio_entry_1 == related_audio_entry_2
        assert related_image_entry_1 == related_image_entry_2
        assert related_video_entry_1 == related_video_entry_2
        assert related_document_entry_1 == related_document_entry_2

    def test_unused_media_deleted(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_unused_media_deleted.csv",
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

        # Adding media that is referenced in the csv
        audio_in_csv = factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_unused_media_deleted_audio.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        doc_in_csv = factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_unused_media_deleted_doc.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        image_in_csv = factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_unused_media_deleted_image.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        video_in_csv = factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_unused_media_deleted_video.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )

        # Adding additional media that is not in the csv
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_unused_media_deleted_audio_2.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_unused_media_deleted_doc_2.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_unused_media_deleted_image_2.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_unused_media_deleted_video_2.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )

        confirm_import_job(import_job.id)

        images = ImageFile.objects.filter(import_job_id=import_job.id)
        files = File.objects.filter(import_job_id=import_job.id)
        videos = VideoFile.objects.filter(import_job_id=import_job.id)

        # Verifying only media included in csv are present after import job completion
        file_ids = list(files.values_list("id", flat=True))

        assert images.count() == 1 and images[0].id == image_in_csv.id
        assert files.count() == 2
        assert audio_in_csv.id in file_ids and doc_in_csv.id in file_ids
        assert videos.count() == 1 and videos[0].id == video_in_csv.id

    def test_exception_deleting_unused_media(self, caplog):
        # Simulating a general exception when deleting unused media files

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_exception_deleting_unused_media.csv",
            mimetype=self.MIMETYPE,
        )
        file = factories.FileFactory(content=file_content)
        import_job = factories.ImportJobFactory(
            site=self.site,
            run_as_user=self.user,
            data=file,
            status=JobStatus.ACCEPTED,
            validation_status=JobStatus.COMPLETE,
        )

        mock_objects = MagicMock()
        mock_objects.delete.side_effect = Exception("General Exception")
        with patch(
            "backend.tasks.import_job_tasks.File.objects.filter",
            return_value=mock_objects,
        ):
            confirm_import_job(import_job.id)

        assert (
            "An exception occurred while trying to delete unused media files."
            in caplog.text
        )

        updated_import_job = ImportJob.objects.filter(id=import_job.id).first()
        assert updated_import_job.status == JobStatus.COMPLETE

    def test_related_media_ids_multiple(self):
        sample_audio_ids = [
            "4cee867a-5069-4169-afe1-5cf6a5d57b3d",
            "74b4a276-6ae6-4de2-9bf5-2d666e493b1a",
        ]
        sample_image_ids = [
            "0259d195-310a-4c95-9980-c94ac5e88d11",
            "d5e3c392-45f3-44db-babe-55d3216b1fc5",
        ]
        sample_video_ids = [
            "e651860b-a3cc-4607-87a1-c767125900ef",
            "1bcd5d10-ad0b-4810-89a3-f307c0b967c5",
        ]
        sample_doc_ids = [
            "85211bdc-695a-416b-a432-7772476e6ad2",
            "6fdb1445-990f-47ce-bd4d-970dda685b28",
        ]

        factories.AudioFactory.create(id=sample_audio_ids[0], site=self.site)
        factories.AudioFactory.create(id=sample_audio_ids[1], site=self.site)
        factories.ImageFactory.create(id=sample_image_ids[0], site=self.site)
        factories.ImageFactory.create(id=sample_image_ids[1], site=self.site)
        factories.VideoFactory.create(id=sample_video_ids[0], site=self.site)
        factories.VideoFactory.create(id=sample_video_ids[1], site=self.site)
        factories.DocumentFactory.create(id=sample_doc_ids[0], site=self.site)
        factories.DocumentFactory.create(id=sample_doc_ids[1], site=self.site)

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_ids_multiple.csv",
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
        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 5
        entry1 = DictionaryEntry.objects.get(
            title="test_related_media_ids_multiple_audio"
        )
        assert entry1.related_audio.filter(id__in=sample_audio_ids).count() == 2

        entry2 = DictionaryEntry.objects.get(
            title="test_related_media_ids_multiple_images"
        )
        assert entry2.related_images.filter(id__in=sample_image_ids).count() == 2

        entry3 = DictionaryEntry.objects.get(
            title="test_related_media_ids_multiple_videos"
        )
        assert entry3.related_videos.filter(id__in=sample_video_ids).count() == 2

        entry4 = DictionaryEntry.objects.get(
            title="test_related_media_ids_multiple_docs"
        )
        assert entry4.related_documents.filter(id__in=sample_doc_ids).count() == 2

        entry5 = DictionaryEntry.objects.get(
            title="test_related_media_ids_multiple_all"
        )
        assert entry5.related_audio.filter(id__in=sample_audio_ids).count() == 2
        assert entry5.related_images.filter(id__in=sample_image_ids).count() == 2
        assert entry5.related_videos.filter(id__in=sample_video_ids).count() == 2
        assert entry5.related_documents.filter(id__in=sample_doc_ids).count() == 2

    def test_related_media_mixed_multiple(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_mixed_multiple.csv",
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

        sample_audio_ids = [
            "5eea7169-77a3-46a7-8048-72ea835eaacf",
            "59d2047b-52ba-496e-b748-7dbaec745c9e",
        ]
        sample_image_ids = [
            "12dd14fd-49f2-4cc7-8e13-d3d3ca28afc4",
            "fe894b42-081d-4482-bec0-cd64ca8409d0",
        ]
        sample_video_ids = [
            "828c6a5d-d862-41c3-940b-3132ca4125ae",
            "fd29eff9-2207-446a-9f2c-203124cbb7ed",
        ]
        sample_doc_ids = [
            "18f4b9c0-a938-4912-9dc0-8a0f199c2774",
            "ff10acb6-f88b-42ec-bca0-3b05ee90efb4",
        ]
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_mixed_multiple_image.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.ImageFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_mixed_multiple_image_2.jpg",
                mimetype="image/jpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_mixed_multiple_audio.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_mixed_multiple_audio_2.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_mixed_multiple_video.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )
        factories.VideoFileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_mixed_multiple_video_2.mp4",
                mimetype="video/mp4",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_mixed_multiple_doc.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_related_media_mixed_multiple_doc_2.pdf",
                mimetype="application/pdf",
            ),
            import_job=import_job,
        )

        factories.AudioFactory.create(id=sample_audio_ids[0], site=self.site)
        factories.AudioFactory.create(id=sample_audio_ids[1], site=self.site)
        factories.DocumentFactory.create(id=sample_doc_ids[0], site=self.site)
        factories.DocumentFactory.create(id=sample_doc_ids[1], site=self.site)
        factories.ImageFactory.create(id=sample_image_ids[0], site=self.site)
        factories.ImageFactory.create(id=sample_image_ids[1], site=self.site)
        factories.VideoFactory.create(id=sample_video_ids[0], site=self.site)
        factories.VideoFactory.create(id=sample_video_ids[1], site=self.site)

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 5
        entry1 = DictionaryEntry.objects.get(
            title="test_related_media_mixed_multiple_audio"
        )
        assert entry1.related_audio.filter(id__in=sample_audio_ids).count() == 2
        assert entry1.related_audio.count() == 4

        entry2 = DictionaryEntry.objects.get(
            title="test_related_media_mixed_multiple_image"
        )
        assert entry2.related_images.filter(id__in=sample_image_ids).count() == 2
        assert entry2.related_images.count() == 4

        entry3 = DictionaryEntry.objects.get(
            title="test_related_media_mixed_multiple_video"
        )
        assert entry3.related_videos.filter(id__in=sample_video_ids).count() == 2
        assert entry3.related_videos.count() == 4

        entry4 = DictionaryEntry.objects.get(
            title="test_related_media_mixed_multiple_doc"
        )
        assert entry4.related_documents.filter(id__in=sample_doc_ids).count() == 2
        assert entry4.related_documents.count() == 4

        entry5 = DictionaryEntry.objects.get(
            title="test_related_media_mixed_multiple_all_media"
        )
        assert entry5.related_audio.filter(id__in=sample_audio_ids).count() == 2
        assert entry5.related_audio.count() == 4
        assert entry5.related_images.filter(id__in=sample_image_ids).count() == 2
        assert entry5.related_images.count() == 4
        assert entry5.related_videos.filter(id__in=sample_video_ids).count() == 2
        assert entry5.related_videos.count() == 4
        assert entry5.related_documents.filter(id__in=sample_doc_ids).count() == 2
        assert entry5.related_documents.count() == 4

    def test_related_media_duplicate_ids(self):
        sample_audio_id = "cd03befe-0910-4d39-8d16-e969ba589f40"
        sample_image_id = "d7b5d063-e9e3-4d6b-bc16-ba3c4e9e856b"
        sample_video_id = "46c4530f-9d4e-416c-822e-03df81991396"
        sample_doc_id = "b1836222-c901-4ed7-b082-13d05bc2d23a"

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_duplicate_ids_confirm_import.csv",
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
        factories.AudioFactory.create(id=sample_audio_id, site=self.site)
        factories.DocumentFactory.create(id=sample_doc_id, site=self.site)
        factories.ImageFactory.create(id=sample_image_id, site=self.site)
        factories.VideoFactory.create(id=sample_video_id, site=self.site)
        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 5
        entry1 = DictionaryEntry.objects.get(
            title="test_related_media_duplicate_ids_duplicate_audio"
        )
        assert entry1.related_audio.filter(id=sample_audio_id).count() == 1
        assert entry1.related_audio.count() == 1

        entry2 = DictionaryEntry.objects.get(
            title="test_related_media_duplicate_ids_duplicate_image"
        )
        assert entry2.related_images.filter(id=sample_image_id).count() == 1
        assert entry2.related_images.count() == 1

        entry3 = DictionaryEntry.objects.get(
            title="test_related_media_duplicate_ids_duplicate_video"
        )
        assert entry3.related_videos.filter(id=sample_video_id).count() == 1
        assert entry3.related_videos.count() == 1

        entry4 = DictionaryEntry.objects.get(
            title="test_related_media_duplicate_ids_duplicate_doc"
        )
        assert entry4.related_documents.filter(id=sample_doc_id).count() == 1
        assert entry4.related_documents.count() == 1

        entry5 = DictionaryEntry.objects.get(
            title="test_related_media_duplicate_ids_duplicate_all"
        )
        assert entry5.related_audio.filter(id=sample_audio_id).count() == 1
        assert entry5.related_audio.count() == 1
        assert entry5.related_images.filter(id=sample_image_id).count() == 1
        assert entry5.related_images.count() == 1
        assert entry5.related_videos.filter(id=sample_video_id).count() == 1
        assert entry5.related_videos.count() == 1
        assert entry5.related_documents.filter(id=sample_doc_id).count() == 1
        assert entry5.related_documents.count() == 1

    def test_related_media_id_mixed_invalid_and_valid(self):
        sample_audio_id = "8f601ae2-da53-4f8d-bde2-f57e0ed1a54b"
        sample_image_id = "3c578433-236b-4039-8486-fecc61ca4784"
        sample_video_id = "72fda2e6-6343-4c45-abd3-903e8b2e1614"
        sample_doc_id = "391b21d7-50db-499f-bf09-c7190b21d5b5"

        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_id_mixed_invalid_and_valid.csv",
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
        factories.AudioFactory.create(id=sample_audio_id, site=self.site)
        factories.DocumentFactory.create(id=sample_doc_id, site=self.site)
        factories.ImageFactory.create(id=sample_image_id, site=self.site)
        factories.VideoFactory.create(id=sample_video_id, site=self.site)
        confirm_import_job(import_job.id)

        # All rows have invalid media ids, so no entries should be imported
        assert DictionaryEntry.objects.all().count() == 0

    def test_duplicate_filenames_in_same_row(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_duplicate_filenames_in_same_row.csv",
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
                filename="test_duplicate_filenames_in_same_row_audio.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )
        factories.FileFactory(
            site=self.site,
            content=get_sample_file(
                file_dir=self.MEDIA_FILES_DIR,
                filename="test_duplicate_filenames_in_same_row_audio_2.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )

        confirm_import_job(import_job.id)

        assert DictionaryEntry.objects.all().count() == 1
        entry = DictionaryEntry.objects.get(
            title="test_duplicate_filenames_in_same_row_word_1"
        )
        assert entry.related_audio.count() == 2

    def test_related_media_multiple_invalid(self):
        file_content = get_sample_file(
            file_dir=self.CSV_FILES_DIR,
            filename="test_related_media_multiple_invalid.csv",
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
                filename="test_related_media_multiple_invalid_audio.mp3",
                mimetype="audio/mpeg",
            ),
            import_job=import_job,
        )

        confirm_import_job(import_job.id)
        assert DictionaryEntry.objects.filter(site=self.site).count() == 0
