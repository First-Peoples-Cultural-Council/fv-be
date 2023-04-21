from backend.models.constants import AppRole
from backend.models.sites import Site
from backend.models.utils import load_data
from backend.tests.factories import get_app_admin


class TestSiteModel:
    """
    Tests for Site model.
    """

    def test_adding_default_categories(self, db):
        """Verify the number of default categories being added when a site is created."""
        admin_user = get_app_admin(AppRole.STAFF)
        site = Site(
            title="Site 1",
            slug="site_1",
            created_by=admin_user,
            last_modified_by=admin_user,
        )
        site.save()
        categories = site.category_set.all()
        default_categories = load_data("default_categories.json")

        assert len(default_categories) == len(categories)
