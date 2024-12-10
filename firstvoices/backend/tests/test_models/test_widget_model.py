import pytest
from django.db import IntegrityError

from backend.tests import factories


class TestSiteWidgetListModel:
    @pytest.mark.django_db
    def test_site_widget_unique_for_site_widget_list(self):
        site = factories.SiteFactory.create()
        widget_one = factories.SiteWidgetFactory.create(site=site)
        site_widget_list = factories.SiteWidgetListFactory.create(site=site)

        factories.SiteWidgetListOrderFactory.create(
            site_widget=widget_one, site_widget_list=site_widget_list, order=1
        )

        with pytest.raises(IntegrityError):
            factories.SiteWidgetListOrderFactory.create(
                site_widget=widget_one, site_widget_list=site_widget_list, order=2
            )
            pytest.fail(
                "Expected error when trying to add a duplicate SiteWidget to a SiteWidgetList."
            )
