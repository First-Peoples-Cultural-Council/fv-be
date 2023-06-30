import pytest
from django.db import IntegrityError

from backend.tests import factories


class TestSiteWidgetListModel:
    @pytest.mark.django_db
    def test_unique_order(self):
        site_widget_list = factories.SiteWidgetListWithTwoWidgetsFactory.create()

        widget_one_order = site_widget_list.sitewidgetlistorder_set.all()[0]
        widget_two_order = site_widget_list.sitewidgetlistorder_set.all()[1]
        assert widget_one_order.order == 0
        assert widget_two_order.order == 1

        with pytest.raises(IntegrityError):
            widget_two_order.order = 0
            widget_two_order.save()
            pytest.fail("Expected IntegrityError due to non-unique order values.")
