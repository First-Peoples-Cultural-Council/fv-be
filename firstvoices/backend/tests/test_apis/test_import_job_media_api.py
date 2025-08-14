import json
import uuid

import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.models.files import File
from backend.models.jobs import JobStatus
from backend.models.media import ImageFile, VideoFile
from backend.tests.factories import FileFactory, ImportJobFactory, get_site_with_member
from backend.tests.test_apis.base.base_media_test import FormDataMixin
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestImportJobMediaEndpoint(
    FormDataMixin,
):
    # This view has no valid list endpoint for testing
    APP_NAME = "backend"
    UPLOAD_VIEW = "api:importjob-media-list"

    def setup_method(self):
        self.site, self.user = get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )

        file_content = get_sample_file("import_job/all_valid_columns.csv", "text/csv")
        file = FileFactory(content=file_content)
        self.import_job = ImportJobFactory(site=self.site, data=file)

        self.endpoint = reverse(
            self.UPLOAD_VIEW,
            current_app=self.APP_NAME,
            args=[self.site.slug, self.import_job.id],
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_invalid_import_job(self):
        endpoint = reverse(
            self.UPLOAD_VIEW,
            current_app=self.APP_NAME,
            args=[self.site.slug, uuid.uuid4()],
        )
        data = {
            "file": [
                get_sample_file("sample-image.jpg", "image/jpeg"),
            ]
        }

        response = self.client.post(
            endpoint,
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 404

    def test_wrong_permissions(self):
        site, user = get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.MEMBER
        )

        file_content = get_sample_file("import_job/all_valid_columns.csv", "text/csv")
        file = FileFactory(content=file_content)
        import_job = ImportJobFactory(site=site, data=file)

        endpoint = reverse(
            self.UPLOAD_VIEW,
            current_app=self.APP_NAME,
            args=[self.site.slug, import_job.id],
        )

        client = APIClient()
        client.force_authenticate(user=user)

        data = {
            "file": [
                get_sample_file("sample-image.jpg", "image/jpeg"),
            ]
        }

        response = client.post(
            endpoint,
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 403

    def test_invalid_file_type(self):
        data = {
            "file": [
                get_sample_file("sample-image.jpg", "image/jpeg"),
                get_sample_file("file.txt", "text/plain"),
                get_sample_file("import_job/Another image.jpg", "image/jpeg"),
            ]
        }

        response = self.client.post(
            self.endpoint,
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400
        response = json.loads(response.content)
        assert "Unsupported filetype. File: file.txt" in response

        # Ensure no media files are created
        images = ImageFile.objects.filter(import_job_id=self.import_job.id)
        assert images.count() == 0

    @pytest.mark.parametrize("job_status", JobStatus.names)
    def test_already_confirmed(self, job_status):
        data = {
            "file": [
                get_sample_file("sample-audio.mp3", "audio/mp3"),
            ]
        }

        self.import_job.status = job_status
        self.import_job.save()

        response = self.client.post(
            self.endpoint,
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400
        response_content = json.loads(response.content)
        assert (
            f"Can't add media after an import job has started. This job already has status: {job_status}."
            in response_content
        )

    def test_upload_valid_files(self):
        data = {
            "file": [
                get_sample_file("sample-image.jpg", "image/jpeg"),
                get_sample_file("sample-audio.mp3", "audio/mp3"),
                get_sample_file("video_example_small.mp4", "video/mp4"),
            ]
        }

        response = self.client.post(
            self.endpoint,
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 202

        # Image
        image_file = ImageFile.objects.first()
        assert image_file.import_job_id == self.import_job.id
        assert "sample-image.jpg" in image_file.content.name

        # Video
        video_file = VideoFile.objects.first()
        assert video_file.import_job_id == self.import_job.id
        assert "video_example_small.mp4" in video_file.content.name

        # Audio
        audio_file = File.objects.filter(mimetype="audio/mpeg").first()
        assert audio_file.import_job_id == self.import_job.id
        assert "sample-audio.mp3" in audio_file.content.name

    def test_upload_duplicate_filename(self):
        data = {
            "file": [
                get_sample_file("video_example_small.mp4", "video/mp4"),
                get_sample_file("sample-image.jpg", "image/jpeg"),
                get_sample_file("sample-image.jpg", "image/jpeg"),
            ]
        }

        response = self.client.post(
            self.endpoint,
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 400
        response_content = json.loads(response.content)
        assert (
            "There are one or more duplicate filenames within your upload."
            in response_content
        )

    def test_subsequent_upload_duplicate_filename(self):
        data = {
            "file": [
                get_sample_file("video_example_small.mp4", "video/mp4"),
                get_sample_file("sample-image.jpg", "image/jpeg"),
            ]
        }

        response = self.client.post(
            self.endpoint,
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 202

        additional_data = {
            "file": [
                get_sample_file("sample-image.jpg", "image/jpeg"),
            ]
        }

        response = self.client.post(
            self.endpoint,
            data=self.format_upload_data(additional_data),
            content_type=self.content_type,
        )

        assert response.status_code == 400
        response_content = json.loads(response.content)
        assert (
            "You cannot upload a file with the same name as one already uploaded to this import job."
            in response_content
        )
