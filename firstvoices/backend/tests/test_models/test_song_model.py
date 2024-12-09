import pytest

from backend.tests.factories import SongFactory
from backend.tests.test_models.test_media_models import RelatedVideoLinksValidationMixin


class TestSongModel(RelatedVideoLinksValidationMixin):
    """
    Tests for Song model.
    """

    def create_instance_with_related_video_links(self, site, related_video_links):
        return SongFactory.create(site=site, related_video_links=related_video_links)

    @pytest.mark.django_db
    def test_html_cleaning_fields(self):
        song = SongFactory.create(
            introduction="<script src=example.com/malicious.js></script><strong>Arm</strong>",
            introduction_translation="<script>alert('XSS');</script>",
        )
        song.save()
        song.refresh_from_db()

        assert song.introduction == "<strong>Arm</strong>"
        assert song.introduction_translation == ""
