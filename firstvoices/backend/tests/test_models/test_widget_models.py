import pytest

from backend.models.constants import Visibility
from backend.models.widget import SiteWidgetListOrder
from backend.tests import factories
from backend.tests.factories import SiteWidgetListWithTwoWidgetsFactory


class TestSiteWidgetListModel:
    @pytest.mark.django_db
    def test_sitewidgetlistorder_sitewidgetlist_site_update(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.SiteWidgetListOrderFactory.reset_sequence()
        widget_list = SiteWidgetListWithTwoWidgetsFactory.create(site=site)

        widget = widget_list.widgets.all()[0]
        order_instance = SiteWidgetListOrder.objects.filter(site_widget=widget).first()
        order_instance_id = order_instance.id

        # Check that the SiteWidgetListOrder instance has the same site as the SiteWidgetList instance
        assert order_instance.site == site

        # Create a second site and update the SiteWidgetList site field
        site_two = factories.SiteFactory.create()
        widget_list.site = site_two
        widget_list.save()

        order_instance = SiteWidgetListOrder.objects.get(id=order_instance_id)

        # Check that the SiteWidgetListOrder instance has the same new site as the SiteWidgetList instance
        assert order_instance.site == site_two

    @pytest.mark.django_db
    def test_sitewidgetlistorder_sitewidget_visibility_update(self):
        site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
        factories.SiteWidgetListOrderFactory.reset_sequence()
        widget_list = SiteWidgetListWithTwoWidgetsFactory.create(site=site)

        widget = widget_list.widgets.all()[0]
        order_instance = SiteWidgetListOrder.objects.filter(site_widget=widget).first()
        widget_visibility = widget.visibility
        order_instance_id = order_instance.id

        assert widget_visibility == Visibility.PUBLIC

        # Check that the SiteWidgetListOrder visibility matches the SiteWidget visibility
        assert order_instance.visibility == widget_visibility

        # Update the SiteWidget visibility field
        widget.visibility = Visibility.TEAM
        widget.save()

        order_instance = SiteWidgetListOrder.objects.get(id=order_instance_id)

        # Check that the SiteWidgetListOrder visibility matches the SiteWidget new visibility
        assert order_instance.visibility == Visibility.TEAM
