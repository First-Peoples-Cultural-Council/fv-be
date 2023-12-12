from backend.tests.factories import StoryFactory
from backend.tests.test_models.test_media_models import RelatedVideoLinksValidationMixin


class TestStoryModel(RelatedVideoLinksValidationMixin):
    """
    Tests for Song model.
    """

    def create_instance_with_related_video_links(self, site, related_video_links):
        return StoryFactory.create(site=site, related_video_links=related_video_links)
