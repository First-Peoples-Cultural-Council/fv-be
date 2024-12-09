import pytest

from backend.tests.factories import StoryFactory
from backend.tests.test_models.test_media_models import RelatedVideoLinksValidationMixin


class TestStoryModel(RelatedVideoLinksValidationMixin):
    """
    Tests for Story model.
    """

    def create_instance_with_related_video_links(self, site, related_video_links):
        return StoryFactory.create(site=site, related_video_links=related_video_links)

    @pytest.mark.django_db
    def test_html_cleaning_fields(self):
        story = StoryFactory.create(
            introduction="<script src=example.com/malicious.js></script><strong>Arm</strong>",
            introduction_translation="<script>alert('XSS');</script>",
        )
        story.save()
        story.refresh_from_db()

        assert story.introduction == "<strong>Arm</strong>"
        assert story.introduction_translation == ""
