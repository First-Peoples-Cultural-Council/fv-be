import re

import pytest
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from backend.models.constants import Role, Visibility
from backend.models.files import File
from backend.models.media import ImageFile, VideoFile
from backend.tests.factories import FileFactory, UpdateJobFactory, get_site_with_member
from backend.tests.test_apis.base.import_update_jobs.base_media_endpoint_test import (
    BaseImportUpdateJobMediaEndpoint,
)
from backend.tests.utils import get_sample_file


@pytest.mark.django_db
class TestUpdateJobMediaEndpoint(
    BaseImportUpdateJobMediaEndpoint,
):
    APP_NAME = "backend"
    UPLOAD_VIEW = "api:updatejob-media-list"

    def setup_method(self):
        self.site, self.user = get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )

        file_content = get_sample_file("update_job/minimal.csv", "text/csv")
        file = FileFactory(content=file_content)
        self.import_job = UpdateJobFactory(site=self.site, data=file)

        self.endpoint = reverse(
            self.UPLOAD_VIEW,
            current_app=self.APP_NAME,
            args=[self.site.slug, self.import_job.id],
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_wrong_permissions(self):
        site, user = get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.MEMBER
        )

        file_content = get_sample_file("update_job/minimal.csv", "text/csv")
        file = FileFactory(content=file_content)
        import_job = UpdateJobFactory(site=site, data=file)

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
        assert image_file.update_job_id == self.import_job.id
        assert image_file.import_job_id is None
        assert re.search(r"sample-image(_\w+)?\.jpg", image_file.content.name)

        # Video
        video_file = VideoFile.objects.first()
        assert video_file.update_job_id == self.import_job.id
        assert video_file.import_job_id is None
        assert re.search(r"video_example_small(_\w+)?\.mp4", video_file.content.name)

        # Audio
        audio_file = File.objects.filter(mimetype="audio/mpeg").first()
        assert audio_file.update_job_id == self.import_job.id
        assert audio_file.import_job_id is None
        assert re.search(r"sample-audio(_\w+)?\.mp3", audio_file.content.name)
