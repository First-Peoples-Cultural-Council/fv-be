import pytest
from django.db import IntegrityError

from backend.models.constants import WIDGET_ALPHABET, WIDGET_STATS, WIDGET_WOTD, AppRole
from backend.models.sites import Site
from backend.models.utils import load_data
from backend.tests import factories
from backend.tests.factories import get_app_admin


class TestSiteModel:
    """
    Tests for Site model.
    """

    TEST_SITE_TITLE = "Site 1"
    TEST_SITE_SLUG = "site_1"

    def test_adding_default_categories(self, db):
        """Verify the number of default categories being added when a site is created."""
        admin_user = get_app_admin(AppRole.STAFF)
        site = Site(
            title=self.TEST_SITE_TITLE,
            slug=self.TEST_SITE_SLUG,
            created_by=admin_user,
            last_modified_by=admin_user,
        )
        site.save()
        categories = site.category_set.all()
        default_categories = load_data("default_categories.json")

        assert len(default_categories) == len(categories)

    def test_adding_default_widgets(self, db):
        """Verify the default widgets are added when a site is created."""
        admin_user = get_app_admin(AppRole.STAFF)
        site = Site(
            title=self.TEST_SITE_TITLE,
            slug=self.TEST_SITE_SLUG,
            created_by=admin_user,
            last_modified_by=admin_user,
        )
        site.save()
        widgets_count = site.sitewidget_set.count()
        widget_types = site.sitewidget_set.values_list("widget_type", flat=True)

        assert widgets_count == 3
        assert WIDGET_ALPHABET in widget_types
        assert WIDGET_STATS in widget_types
        assert WIDGET_WOTD in widget_types

    @pytest.mark.django_db
    def test_only_one_banner(self):
        """Verify that you can't add both a banner image and a banner video."""
        admin_user = get_app_admin(AppRole.STAFF)
        video = factories.VideoFactory()
        image = factories.ImageFactory()

        site = Site(
            title=self.TEST_SITE_TITLE,
            slug=self.TEST_SITE_SLUG,
            created_by=admin_user,
            last_modified_by=admin_user,
            banner_image=image,
            banner_video=video,
        )

        with pytest.raises(IntegrityError):
            site.save()

    @pytest.mark.django_db
    def test_metadata_onsave(self):
        admin_user = get_app_admin(AppRole.STAFF)
        site = Site(
            title=self.TEST_SITE_TITLE,
            slug=self.TEST_SITE_SLUG,
            created_by=admin_user,
            last_modified_by=admin_user,
        )
        site.save()

        site.title = self.TEST_SITE_TITLE * 2
        site.save()

        fetched_site = Site.objects.get(id=site.id)
        assert fetched_site.created != fetched_site.last_modified
