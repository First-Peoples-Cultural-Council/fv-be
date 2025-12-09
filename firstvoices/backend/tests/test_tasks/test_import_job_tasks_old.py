# import uuid
# from unittest.mock import MagicMock, patch
# from uuid import UUID
#
# import pytest
# import tablib
# from django.utils.text import get_valid_filename
# import random
# from datetime import datetime
# from django.utils import timezone
# import os
# from django.core.cache import cache
#
# from backend.models import DictionaryEntry, ImportJob
# from backend.models.constants import Visibility
# from backend.models.dictionary import (
#     ExternalDictionaryEntrySystem,
#     TypeOfDictionaryEntry,
# )
# from backend.models.files import File
# from backend.models.import_jobs import JobStatus
# from backend.models.media import ImageFile, VideoFile
# from backend.tasks.import_job_tasks import confirm_import_job, validate_import_job
# from backend.tests import factories
# from backend.tests.test_tasks.base_task_test import IgnoreTaskResultsMixin

# from backend.tests.utils import get_sample_file

# @pytest.mark.django_db
# class TestBulkImport(IgnoreTaskResultsMixin):
#     MIMETYPE = "text/csv"
#     TASK = confirm_import_job
#
#     ACKNOWLEDGEMENT = "Test Ack"
#     AUDIO_TITLE = "Related Audio"
#     AUDIO_DESCRIPTION = "Testing audio upload"
#     DOCUMENT_TITLE = "Related Document"
#     DOCUMENT_DESCRIPTION = "Testing document upload"
#     IMAGE_TITLE = "Related Image"
#     IMAGE_DESCRIPTION = "Testing image upload"
#     TEST_SPEAKER = "Test Speaker"
#     VIDEO_TITLE = "Related Video"
#     VIDEO_DESCRIPTION = "Testing video upload"
#
#     def get_valid_task_args(self):
#         return (uuid.uuid4(),)
#
#     def confirm_upload_with_media_files(self, filename):
#         factories.PersonFactory.create(name=f"{self.TEST_SPEAKER} 1", site=self.site)
#         factories.PersonFactory.create(name=f"{self.TEST_SPEAKER} 2", site=self.site)
#         factories.FileFactory(
#             site=self.site,
#             content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
#             import_job=import_job,
#         )
#         factories.FileFactory(
#             site=self.site,
#             content=get_sample_file("import_job/Another audio.mp3", "audio/mpeg"),
#             import_job=import_job,
#         )
#         factories.FileFactory(
#             site=self.site,
#             content=get_sample_file("sample-document.pdf", "application/pdf"),
#             import_job=import_job,
#         )
#         factories.FileFactory(
#             site=self.site,
#             content=get_sample_file(
#                 "import_job/Another document.pdf", "application/pdf"
#             ),
#             import_job=import_job,
#         )
#         factories.VideoFileFactory(
#             site=self.site,
#             content=get_sample_file("video_example_small.mp4", "video/mp4"),
#             import_job=import_job,
#         )
#         factories.VideoFileFactory(
#             site=self.site,
#             content=get_sample_file("import_job/Another video.mp4", "video/mp4"),
#             import_job=import_job,
#         )
#
#         confirm_import_job(import_job.id)
#         return import_job
#
#     def upload_multiple_media_files(self, count, filename, file_type, import_job):
#         if file_type == "audio":
#             base_file = "sample-audio.mp3"
#             file_ext = ".mp3"
#             media_factory = factories.FileFactory
#             mimetype = "audio/mpeg"
#         elif file_type == "image":
#             base_file = "sample-image.jpg"
#             file_ext = ".jpg"
#             media_factory = factories.ImageFileFactory
#             mimetype = "image/jpeg"
#         elif file_type == "video":
#             base_file = "video_example_small.mp4"
#             file_ext = ".mp4"
#             media_factory = factories.VideoFileFactory
#             mimetype = "video/mp4"
#         elif file_type == "document":
#             base_file = "sample-document.pdf"
#             file_ext = ".pdf"
#             media_factory = factories.FileFactory
#             mimetype = "application/pdf"
#         else:
#             return
#
#         for x in range(1, count + 1):
#             media_factory(
#                 site=self.site,
#                 content=get_sample_file(
#                     filename=f"{base_file}",
#                     mimetype=mimetype,
#                     title=f"{filename}-{x}{file_ext}",
#                 ),
#                 import_job=import_job,
#             )
#
#     def assert_related_media_details(self, related_media, suffix_number=""):
#         assert related_media.acknowledgement == f"{self.ACKNOWLEDGEMENT}{suffix_number}"
#         assert related_media.exclude_from_kids is False
#
#     def assert_related_audio_details(self, filename, related_audio, suffix_number=""):
#         assert f"{filename}{suffix_number}.mp3" in related_audio.original.content.name
#         assert related_audio.title == f"{self.AUDIO_TITLE}{suffix_number}"
#         assert related_audio.description == f"{self.AUDIO_DESCRIPTION}{suffix_number}"
#         assert related_audio.exclude_from_games is True
#         self.assert_related_media_details(related_audio, suffix_number)
#
#     def assert_related_document_details(
#         self, filename, related_document, suffix_number=""
#     ):
#         assert (
#             f"{filename}{suffix_number}.pdf" in related_document.original.content.name
#         )
#         assert related_document.title == f"{self.DOCUMENT_TITLE}{suffix_number}"
#         assert (
#             related_document.description
#             == f"{self.DOCUMENT_DESCRIPTION}{suffix_number}"
#         )
#         assert related_document.exclude_from_games is False
#         self.assert_related_media_details(related_document, suffix_number)
#
#     def assert_related_image_details(self, filename, related_image, suffix_number=""):
#         assert f"{filename}{suffix_number}.jpg" in related_image.original.content.name
#         assert related_image.title == f"{self.IMAGE_TITLE}{suffix_number}"
#         assert related_image.description == f"{self.IMAGE_DESCRIPTION}{suffix_number}"
#         assert related_image.exclude_from_games is False
#         self.assert_related_media_details(related_image, suffix_number)
#
#     def assert_related_video_details(self, filename, related_video, suffix_number=""):
#         assert f"{filename}{suffix_number}.mp4" in related_video.original.content.name
#         assert related_video.title == f"{self.VIDEO_TITLE}{suffix_number}"
#         assert related_video.description == f"{self.VIDEO_DESCRIPTION}{suffix_number}"
#         assert related_video.exclude_from_games is False
#         self.assert_related_media_details(related_video, suffix_number)
#
#     def assert_max_speakers(self, related_audio, suffix_number):
#         assert related_audio.speakers.count() == 5
#         expected_speakers = [
#             f"{self.TEST_SPEAKER} {suffix_number}-{i}" for i in range(1, 6)
#         ]
#         actual_speakers = list(related_audio.speakers.values_list("name", flat=True))
#         assert all(speaker in actual_speakers for speaker in expected_speakers)
#     def test_related_media_full(self):
#         file_content = get_sample_file(
#             "import_job/related_media_full.csv", self.MIMETYPE
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.COMPLETE,
#             status=JobStatus.ACCEPTED,
#         )
#
#         self.upload_multiple_media_files(5, "related_audio", "audio", import_job)
#         self.upload_multiple_media_files(5, "related_image", "image", import_job)
#         self.upload_multiple_media_files(5, "related_video", "video", import_job)
#         self.upload_multiple_media_files(5, "related_document", "document", import_job)
#
#         for x in range(1, 6):
#             for z in range(1, 6):
#                 factories.PersonFactory.create(
#                     name=f"Test Speaker {x}-{z}", site=self.site
#                 )
#
#         confirm_import_job(import_job.id)
#
#         entry_1 = DictionaryEntry.objects.get(title="Word 1")
#         related_audio_1 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-1")
#         self.assert_related_audio_details("related_audio", related_audio_1, "-1")
#         self.assert_max_speakers(related_audio_1, "1")
#         related_audio_2 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-2")
#         self.assert_related_audio_details("related_audio", related_audio_2, "-2")
#         self.assert_max_speakers(related_audio_2, "2")
#         related_audio_3 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-3")
#         self.assert_related_audio_details("related_audio", related_audio_3, "-3")
#         self.assert_max_speakers(related_audio_3, "3")
#         related_audio_4 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-4")
#         self.assert_related_audio_details("related_audio", related_audio_4, "-4")
#         self.assert_max_speakers(related_audio_4, "4")
#         related_audio_5 = entry_1.related_audio.get(title=f"{self.AUDIO_TITLE}-5")
#         self.assert_related_audio_details("related_audio", related_audio_5, "-5")
#         self.assert_max_speakers(related_audio_5, "5")
#
#         related_image_1 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-1")
#         self.assert_related_image_details("related_image", related_image_1, "-1")
#         related_image_2 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-2")
#         self.assert_related_image_details("related_image", related_image_2, "-2")
#         related_image_3 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-3")
#         self.assert_related_image_details("related_image", related_image_3, "-3")
#         related_image_4 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-4")
#         self.assert_related_image_details("related_image", related_image_4, "-4")
#         related_image_5 = entry_1.related_images.get(title=f"{self.IMAGE_TITLE}-5")
#         self.assert_related_image_details("related_image", related_image_5, "-5")
#
#         related_video_1 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-1")
#         self.assert_related_video_details("related_video", related_video_1, "-1")
#         related_video_2 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-2")
#         self.assert_related_video_details("related_video", related_video_2, "-2")
#         related_video_3 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-3")
#         self.assert_related_video_details("related_video", related_video_3, "-3")
#         related_video_4 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-4")
#         self.assert_related_video_details("related_video", related_video_4, "-4")
#         related_video_5 = entry_1.related_videos.get(title=f"{self.VIDEO_TITLE}-5")
#         self.assert_related_video_details("related_video", related_video_5, "-5")
#
#         related_document_1 = entry_1.related_documents.get(
#             title=f"{self.DOCUMENT_TITLE}-1"
#         )
#         self.assert_related_document_details(
#             "related_document", related_document_1, "-1"
#         )
#         related_document_2 = entry_1.related_documents.get(
#             title=f"{self.DOCUMENT_TITLE}-2"
#         )
#         self.assert_related_document_details(
#             "related_document", related_document_2, "-2"
#         )
#         related_document_3 = entry_1.related_documents.get(
#             title=f"{self.DOCUMENT_TITLE}-3"
#         )
#         self.assert_related_document_details(
#             "related_document", related_document_3, "-3"
#         )
#         related_document_4 = entry_1.related_documents.get(
#             title=f"{self.DOCUMENT_TITLE}-4"
#         )
#         self.assert_related_document_details(
#             "related_document", related_document_4, "-4"
#         )
#         related_document_5 = entry_1.related_documents.get(
#             title=f"{self.DOCUMENT_TITLE}-5"
#         )
#         self.assert_related_document_details(
#             "related_document", related_document_5, "-5"
#         )
#
#     def test_media_title_defaults_to_filename(self):
#         self.confirm_upload_with_media_files("minimal_media.csv")
#
#         entry_with_audio = DictionaryEntry.objects.filter(title="Word 1")[0]
#         related_audio = entry_with_audio.related_audio.all()
#         assert related_audio[0].title == "sample-audio.mp3"
#
#         entry_with_image = DictionaryEntry.objects.filter(title="Phrase 1")[0]
#         related_image = entry_with_image.related_images.all()
#         assert related_image[0].title == "sample-image.jpg"
#
#         entry_with_video = DictionaryEntry.objects.filter(title="Word 2")[0]
#         related_video = entry_with_video.related_videos.all()
#         assert related_video[0].title == "video_example_small.mp4"
#
#         entry_with_document = DictionaryEntry.objects.filter(title="Phrase 2")[0]
#         related_document = entry_with_document.related_documents.all()
#         assert related_document[0].title == "sample-document.pdf"
#
#     def test_duplicate_media_filenames(self):
#         # If multiple rows have same filenames, only the first media instance will be imported
#         # and used. The rest of the media will not be imported and should not give any issues.
#         # All the latter entries will use the first imported media file.
#         file_content = get_sample_file(
#             "import_job/duplicate_media_filenames.csv", self.MIMETYPE
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.COMPLETE,
#             status=JobStatus.ACCEPTED,
#         )
#         factories.FileFactory(
#             site=self.site,
#             content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
#             import_job=import_job,
#         )
#         factories.FileFactory(
#             site=self.site,
#             content=get_sample_file("sample-document.pdf", "application/pdf"),
#             import_job=import_job,
#         )
#         factories.ImageFileFactory(
#             site=self.site,
#             content=get_sample_file("sample-image.jpg", "image/jpeg"),
#             import_job=import_job,
#         )
#         factories.VideoFileFactory(
#             site=self.site,
#             content=get_sample_file("video_example_small.mp4", "video/mp4"),
#             import_job=import_job,
#         )
#         factories.PersonFactory.create(name="Test Speaker 1", site=self.site)
#         factories.PersonFactory.create(name="Test Speaker 2", site=self.site)
#
#         confirm_import_job(import_job.id)
#
#         entry_1 = DictionaryEntry.objects.filter(title="Word 1")[0]
#         related_audio_entry_1 = entry_1.related_audio.first()
#         related_document_entry_1 = entry_1.related_documents.first()
#         related_image_entry_1 = entry_1.related_images.first()
#         related_video_entry_1 = entry_1.related_videos.first()
#
#         entry_2 = DictionaryEntry.objects.filter(title="Phrase 1")[0]
#         related_audio_entry_2 = entry_2.related_audio.first()
#         related_document_entry_2 = entry_2.related_documents.first()
#         related_image_entry_2 = entry_2.related_images.first()
#         related_video_entry_2 = entry_2.related_videos.first()
#
#         entry_3 = DictionaryEntry.objects.filter(title="Word 2")[0]
#         related_audio_entry_3 = entry_3.related_audio.first()
#         related_document_entry_3 = entry_3.related_documents.first()
#         related_image_entry_3 = entry_3.related_images.first()
#         related_video_entry_3 = entry_3.related_videos.first()
#
#         assert related_audio_entry_1 == related_audio_entry_2 == related_audio_entry_3
#         assert related_image_entry_1 == related_image_entry_2 == related_image_entry_3
#         assert related_video_entry_1 == related_video_entry_2 == related_video_entry_3
#         assert (
#             related_document_entry_1
#             == related_document_entry_2
#             == related_document_entry_3
#         )
#
#     def test_unused_media_deleted(self):
#         file_content = get_sample_file("import_job/minimal_media.csv", self.MIMETYPE)
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.COMPLETE,
#             status=JobStatus.ACCEPTED,
#         )
#
#         # Adding media that is referenced in the csv
#         audio_in_csv = factories.FileFactory(
#             site=self.site,
#             content=get_sample_file("sample-audio.mp3", "audio/mpeg"),
#             import_job=import_job,
#         )
#
#         document_in_csv = factories.FileFactory(
#             site=self.site,
#             content=get_sample_file("sample-document.pdf", "application/pdf"),
#             import_job=import_job,
#         )
#
#         image_in_csv = factories.ImageFileFactory(
#             site=self.site,
#             content=get_sample_file("sample-image.jpg", "image/jpeg"),
#             import_job=import_job,
#         )
#
#         video_in_csv = factories.VideoFileFactory(
#             site=self.site,
#             content=get_sample_file("video_example_small.mp4", "video/mp4"),
#             import_job=import_job,
#         )
#
#         # Adding additional media that is not in the csv
#         factories.FileFactory(
#             site=self.site,
#             content=get_sample_file("import_job/Another audio.mp3", "audio/mpeg"),
#             import_job=import_job,
#         )
#
#         factories.FileFactory(
#             site=self.site,
#             content=get_sample_file(
#                 "import_job/Another document.pdf", "application/pdf"
#             ),
#             import_job=import_job,
#         )
#
#         factories.ImageFileFactory(
#             site=self.site,
#             content=get_sample_file("import_job/Another image.jpg", "image/jpeg"),
#             import_job=import_job,
#         )
#
#         factories.VideoFileFactory(
#             site=self.site,
#             content=get_sample_file("import_job/Another video.mp4", "video/mp4"),
#             import_job=import_job,
#         )
#
#         confirm_import_job(import_job.id)
#
#         images = ImageFile.objects.filter(import_job_id=import_job.id)
#         files = File.objects.filter(import_job_id=import_job.id)
#         videos = VideoFile.objects.filter(import_job_id=import_job.id)
#
#         # Verifying only media included in csv are present after import job completion
#         file_ids = list(files.values_list("id", flat=True))
#
#         assert images.count() == 1 and images[0].id == image_in_csv.id
#         assert files.count() == 2
#         assert audio_in_csv.id in file_ids and document_in_csv.id in file_ids
#         assert videos.count() == 1 and videos[0].id == video_in_csv.id
#
#     def test_exception_deleting_unused_media(self, caplog):
#         # Simulating a general exception when deleting unused media files
#
#         file_content = get_sample_file("import_job/minimal.csv", self.MIMETYPE)
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             status=JobStatus.ACCEPTED,
#             validation_status=JobStatus.COMPLETE,
#         )
#
#         mock_objects = MagicMock()
#         mock_objects.delete.side_effect = Exception("General Exception")
#         with patch(
#             "backend.tasks.import_job_tasks.File.objects.filter",
#             return_value=mock_objects,
#         ):
#             confirm_import_job(import_job.id)
#
#         assert (
#             "An exception occurred while trying to delete unused media files."
#             in caplog.text
#         )
#
#         updated_import_job = ImportJob.objects.filter(id=import_job.id).first()
#         assert updated_import_job.status == JobStatus.COMPLETE
#
#     def test_related_media_ids_multiple(self):
#         audio = factories.AudioFactory.create(id=TEST_AUDIO_IDS[0])
#         factories.AudioFactory.create(id=TEST_AUDIO_IDS[1], site=audio.site)
#         factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=audio.site)
#         factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[1], site=audio.site)
#         factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=audio.site)
#         factories.ImageFactory.create(id=TEST_IMAGE_IDS[1], site=audio.site)
#         factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=audio.site)
#         factories.VideoFactory.create(id=TEST_VIDEO_IDS[1], site=audio.site)
#
#         file_content = get_sample_file(
#             "import_job/related_media_ids_multiple.csv", self.MIMETYPE
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=audio.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.ACCEPTED,
#         )
#         validate_import_job(import_job.id)
#
#         import_job = ImportJob.objects.get(id=import_job.id)
#         validation_report = import_job.validation_report
#
#         assert validation_report.error_rows == 0
#         assert validation_report.new_rows == 5
#
#         confirm_import_job(import_job.id)
#
#         assert DictionaryEntry.objects.all().count() == 5
#         entry1 = DictionaryEntry.objects.get(title="Multiple audio")
#         assert entry1.related_audio.filter(id__in=TEST_AUDIO_IDS).count() == 2
#
#         entry2 = DictionaryEntry.objects.get(title="Multiple image")
#         assert entry2.related_images.filter(id__in=TEST_IMAGE_IDS).count() == 2
#
#         entry3 = DictionaryEntry.objects.get(title="Multiple video")
#         assert entry3.related_videos.filter(id__in=TEST_VIDEO_IDS).count() == 2
#
#         entry4 = DictionaryEntry.objects.get(title="Multiple document")
#         assert entry4.related_documents.filter(id__in=TEST_DOCUMENT_IDS).count() == 2
#
#         entry4 = DictionaryEntry.objects.get(title="Multiple all media")
#         assert entry4.related_audio.filter(id__in=TEST_AUDIO_IDS).count() == 2
#         assert entry4.related_images.filter(id__in=TEST_IMAGE_IDS).count() == 2
#         assert entry4.related_videos.filter(id__in=TEST_VIDEO_IDS).count() == 2
#         assert entry4.related_documents.filter(id__in=TEST_DOCUMENT_IDS).count() == 2
#
#     def test_related_media_mixed_multiple(self):
#         file_content = get_sample_file(
#             "import_job/related_media_mixed_multiple.csv", self.MIMETYPE
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.ACCEPTED,
#         )
#
#         self.upload_multiple_media_files(2, "related_audio", "audio", import_job)
#         self.upload_multiple_media_files(2, "related_document", "document", import_job)
#         self.upload_multiple_media_files(2, "related_image", "image", import_job)
#         self.upload_multiple_media_files(2, "related_video", "video", import_job)
#
#         factories.AudioFactory.create(id=TEST_AUDIO_IDS[0], site=self.site)
#         factories.AudioFactory.create(id=TEST_AUDIO_IDS[1], site=self.site)
#         factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=self.site)
#         factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[1], site=self.site)
#         factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=self.site)
#         factories.ImageFactory.create(id=TEST_IMAGE_IDS[1], site=self.site)
#         factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=self.site)
#         factories.VideoFactory.create(id=TEST_VIDEO_IDS[1], site=self.site)
#
#         validate_import_job(import_job.id)
#
#         import_job = ImportJob.objects.get(id=import_job.id)
#         validation_report = import_job.validation_report
#
#         assert validation_report.error_rows == 0
#         assert validation_report.new_rows == 5
#
#         confirm_import_job(import_job.id)
#
#         assert DictionaryEntry.objects.all().count() == 5
#         entry1 = DictionaryEntry.objects.get(title="Multiple audio")
#         assert entry1.related_audio.filter(id__in=TEST_AUDIO_IDS).count() == 2
#         assert entry1.related_audio.count() == 4
#
#         entry2 = DictionaryEntry.objects.get(title="Multiple image")
#         assert entry2.related_images.filter(id__in=TEST_IMAGE_IDS).count() == 2
#         assert entry2.related_images.count() == 4
#
#         entry3 = DictionaryEntry.objects.get(title="Multiple video")
#         assert entry3.related_videos.filter(id__in=TEST_VIDEO_IDS).count() == 2
#         assert entry3.related_videos.count() == 4
#
#         entry4 = DictionaryEntry.objects.get(title="Multiple document")
#         assert entry4.related_documents.filter(id__in=TEST_DOCUMENT_IDS).count() == 2
#         assert entry4.related_documents.count() == 4
#
#         entry5 = DictionaryEntry.objects.get(title="Multiple all media")
#         assert entry5.related_audio.filter(id__in=TEST_AUDIO_IDS).count() == 2
#         assert entry5.related_audio.count() == 4
#         assert entry5.related_images.filter(id__in=TEST_IMAGE_IDS).count() == 2
#         assert entry5.related_images.count() == 4
#         assert entry5.related_videos.filter(id__in=TEST_VIDEO_IDS).count() == 2
#         assert entry5.related_videos.count() == 4
#         assert entry5.related_documents.filter(id__in=TEST_DOCUMENT_IDS).count() == 2
#         assert entry5.related_documents.count() == 4
#
#     def test_import_related_media_id_duplicate_ids(self):
#         file_content = get_sample_file(
#             "import_job/related_media_ids_multiple_duplicate.csv", self.MIMETYPE
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.COMPLETE,
#             status=JobStatus.ACCEPTED,
#         )
#         factories.AudioFactory.create(id=TEST_AUDIO_IDS[0], site=self.site)
#         factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=self.site)
#         factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=self.site)
#         factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=self.site)
#         confirm_import_job(import_job.id)
#
#         assert DictionaryEntry.objects.all().count() == 5
#         entry1 = DictionaryEntry.objects.get(title="Duplicate audio")
#         assert entry1.related_audio.filter(id=TEST_AUDIO_IDS[0]).count() == 1
#         assert entry1.related_audio.count() == 1
#
#         entry2 = DictionaryEntry.objects.get(title="Duplicate image")
#         assert entry2.related_images.filter(id=TEST_IMAGE_IDS[0]).count() == 1
#         assert entry2.related_images.count() == 1
#
#         entry3 = DictionaryEntry.objects.get(title="Duplicate video")
#         assert entry3.related_videos.filter(id=TEST_VIDEO_IDS[0]).count() == 1
#         assert entry3.related_videos.count() == 1
#
#         entry4 = DictionaryEntry.objects.get(title="Duplicate document")
#         assert entry4.related_documents.filter(id=TEST_DOCUMENT_IDS[0]).count() == 1
#         assert entry4.related_documents.count() == 1
#
#         entry5 = DictionaryEntry.objects.get(title="Duplicate all media")
#         assert entry5.related_audio.filter(id=TEST_AUDIO_IDS[0]).count() == 1
#         assert entry5.related_audio.count() == 1
#         assert entry5.related_images.filter(id=TEST_IMAGE_IDS[0]).count() == 1
#         assert entry5.related_images.count() == 1
#         assert entry5.related_videos.filter(id=TEST_VIDEO_IDS[0]).count() == 1
#         assert entry5.related_videos.count() == 1
#         assert entry5.related_documents.filter(id=TEST_DOCUMENT_IDS[0]).count() == 1
#         assert entry5.related_documents.count() == 1
#
#     def test_import_related_media_id_mixed_invalid_and_valid(self):
#         file_content = get_sample_file(
#             "import_job/related_media_ids_multiple.csv", self.MIMETYPE
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.COMPLETE,
#             status=JobStatus.ACCEPTED,
#         )
#         factories.AudioFactory.create(id=TEST_AUDIO_IDS[0], site=self.site)
#         factories.DocumentFactory.create(id=TEST_DOCUMENT_IDS[0], site=self.site)
#         factories.ImageFactory.create(id=TEST_IMAGE_IDS[0], site=self.site)
#         factories.VideoFactory.create(id=TEST_VIDEO_IDS[0], site=self.site)
#         confirm_import_job(import_job.id)
#
#         # All rows have invalid media ids, so no entries should be imported
#         assert DictionaryEntry.objects.all().count() == 0
#
#     def test_import_multiple_media_duplicate_filenames_same_row(self):
#         file_content = get_sample_file(
#             "import_job/related_media_multiple_duplicate_row.csv", self.MIMETYPE
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.ACCEPTED,
#         )
#         self.upload_multiple_media_files(2, "related_audio", "audio", import_job)
#
#         validate_import_job(import_job.id)
#         import_job = ImportJob.objects.get(id=import_job.id)
#         validation_report = import_job.validation_report
#
#         assert validation_report.error_rows == 0
#         assert validation_report.new_rows == 1
#
#         confirm_import_job(import_job.id)
#
#         assert DictionaryEntry.objects.all().count() == 1
#         entry = DictionaryEntry.objects.get(title="Duplicate audio row")
#         assert entry.related_audio.count() == 2
#
#     def test_import_multiple_media_duplicate_filenames_same_col(self):
#         file_content = get_sample_file(
#             "import_job/related_media_multiple_duplicate_col.csv", self.MIMETYPE
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.ACCEPTED,
#         )
#         self.upload_multiple_media_files(4, "related_audio", "audio", import_job)
#
#         validate_import_job(import_job.id)
#         import_job = ImportJob.objects.get(id=import_job.id)
#         validation_report = import_job.validation_report
#
#         assert validation_report.error_rows == 0
#         assert validation_report.new_rows == 3
#
#         confirm_import_job(import_job.id)
#
#         assert DictionaryEntry.objects.all().count() == 3
#         entry1 = DictionaryEntry.objects.get(title="Duplicate audio col 1")
#         assert entry1.related_audio.count() == 3
#         entry2 = DictionaryEntry.objects.get(title="Duplicate audio col 2")
#         assert entry2.related_audio.count() == 2
#         entry3 = DictionaryEntry.objects.get(title="Duplicate audio col 3")
#         assert entry3.related_audio.count() == 3
#
#     def test_import_multiple_media_mixed_invalid_and_valid_filenames(self):
#         file_content = get_sample_file(
#             "import_job/related_media_multiple_invalid.csv",
#             self.MIMETYPE,
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.ACCEPTED,
#         )
#         self.upload_multiple_media_files(1, "related_audio", "audio", import_job)
#
#         validate_import_job(import_job.id)
#         import_job = ImportJob.objects.get(id=import_job.id)
#         validation_report = import_job.validation_report
#
#         assert validation_report.error_rows == 1
#         assert validation_report.new_rows == 0
#
#         confirm_import_job(import_job.id)
#         assert DictionaryEntry.objects.all().count() == 0
#
#     def test_missing_media_multiple_rows_skipped(self):
#         self.confirm_upload_with_media_files("missing_media_multiple.csv")
#         assert DictionaryEntry.objects.all().count() == 0
#
#     def test_import_video_embed_links(self):
#         file_content = get_sample_file(
#             "import_job/video_embed_links.csv", self.MIMETYPE
#         )
#         file = factories.FileFactory(content=file_content)
#         import_job = factories.ImportJobFactory(
#             site=self.site,
#             run_as_user=self.user,
#             data=file,
#             validation_status=JobStatus.COMPLETE,
#             status=JobStatus.ACCEPTED,
#         )
#
#         confirm_import_job(import_job.id)
#
#         assert DictionaryEntry.objects.all().count() == 3
#
#         entry_1 = DictionaryEntry.objects.get(title="YouTube")
#         assert len(entry_1.related_video_links) == 1
#         assert entry_1.related_video_links[0] == YOUTUBE_VIDEO_LINK
#
#         entry_2 = DictionaryEntry.objects.get(title="Vimeo")
#         assert len(entry_2.related_video_links) == 1
#         assert entry_2.related_video_links[0] == VIMEO_VIDEO_LINK
#
#         entry_3 = DictionaryEntry.objects.get(title="Both")
#         assert len(entry_3.related_video_links) == 2
#         assert YOUTUBE_VIDEO_LINK in entry_3.related_video_links
#         assert VIMEO_VIDEO_LINK in entry_3.related_video_links
