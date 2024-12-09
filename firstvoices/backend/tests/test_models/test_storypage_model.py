import pytest

from backend.models.constants import Visibility
from backend.tests import factories
from backend.tests.test_models.test_media_models import RelatedVideoLinksValidationMixin


class TestStoryPageModel(RelatedVideoLinksValidationMixin):
    """
    Tests for StoryPage model.
    """

    def create_instance_with_related_video_links(self, site, related_video_links):
        return factories.StoryPageFactory.create(
            site=site, related_video_links=related_video_links
        )

    @pytest.mark.django_db
    def test_new_page_syncs_with_story(self, db):
        story = factories.StoryFactory.create(visibility=Visibility.TEAM)
        page = factories.StoryPageFactory.create(
            story=story, visibility=Visibility.PUBLIC
        )

        assert page.visibility == story.visibility
        assert page.site == story.site

    @pytest.mark.django_db
    def test_updated_page_syncs_with_story(self, db):
        site = factories.SiteFactory.create()
        story = factories.StoryFactory.create(visibility=Visibility.TEAM, site=site)
        page = factories.StoryPageFactory.create(story=story)

        assert page.visibility == story.visibility
        assert page.site == story.site

        page.visibility = Visibility.MEMBERS
        page.site = factories.SiteFactory.create()
        page.save()

        assert page.visibility == story.visibility
        assert page.site == story.site

    @pytest.mark.django_db
    def test_html_cleaning_fields(self):
        factories.StoryFactory.create()
        page = factories.StoryPageFactory.create(
            text="<script src=example.com/malicious.js></script><strong>Arm</strong>",
            translation="<script>alert('XSS');</script>",
        )
        page.save()
        page.refresh_from_db()

        assert page.text == "<strong>Arm</strong>"
        assert page.translation == ""
