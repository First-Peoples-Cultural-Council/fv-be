import random
import string

from backend.models.constants import Visibility
from backend.models.widget import SiteWidgetListOrder
from backend.tests import factories


def generate_string(length):
    """Function to generate string of ascii characters (both upper and lower case) for the given length."""
    letters = string.ascii_letters
    return "".join(random.choices(letters, k=length))  # NOSONAR


def update_widget_sites(site, widgets):
    for widget in widgets:
        widget.site = site
        widget.save()


def setup_widget_list():
    site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
    factories.SiteWidgetListOrderFactory.reset_sequence()
    widget_list_one = factories.SiteWidgetListWithThreeWidgetsFactory.create(site=site)

    widget_list_two = factories.SiteWidgetListWithThreeWidgetsFactory.create(site=site)

    # Get the widgets from each of the factories.
    widget_one = widget_list_one.widgets.all()[0]
    widget_two = widget_list_one.widgets.all()[1]
    widget_three = widget_list_one.widgets.all()[2]
    widget_two_one = widget_list_two.widgets.all()[0]
    widget_two_two = widget_list_two.widgets.all()[1]
    widget_two_three = widget_list_two.widgets.all()[2]

    widgets = [
        widget_one,
        widget_two,
        widget_three,
        widget_two_one,
        widget_two_two,
        widget_two_three,
    ]
    # Set the widgets to all belong to the same site.
    update_widget_sites(
        site,
        widgets,
    )

    return site, widget_list_one, widget_list_two, widgets


def update_widget_list_order(widgets, widget_list_two):
    # Get the order of the widgets.
    widget_one_list_one_order = SiteWidgetListOrder.objects.filter(
        site_widget=widgets[0]
    ).first()
    widget_two_list_one_order = SiteWidgetListOrder.objects.filter(
        site_widget=widgets[1]
    ).first()
    widget_three_list_one_order = SiteWidgetListOrder.objects.filter(
        site_widget=widgets[2]
    ).first()
    widget_four_list_two_order = SiteWidgetListOrder.objects.filter(
        site_widget=widgets[3]
    ).first()
    widget_five_list_two_order = SiteWidgetListOrder.objects.filter(
        site_widget=widgets[4]
    ).first()
    widget_six_list_two_order = SiteWidgetListOrder.objects.filter(
        site_widget=widgets[5]
    ).first()

    # Update one of the existing widgets order (to free up order 0 in the list)
    widget_five_list_two_order.order = 3
    widget_five_list_two_order.save()

    assert widget_one_list_one_order.order == 2
    assert widget_two_list_one_order.order == 0
    assert widget_three_list_one_order.order == 1
    assert widget_four_list_two_order.order == 2
    widget_five_list_two_order = SiteWidgetListOrder.objects.filter(
        site_widget=widgets[4]
    ).first()  # refresh the five_list_two_order object
    assert widget_five_list_two_order.order == 3
    assert widget_six_list_two_order.order == 1

    # Add a widget from widget_list_one to widget_list_two with a different order
    SiteWidgetListOrder.objects.create(
        site_widget=widgets[0], site_widget_list=widget_list_two, order=0
    )


def find_object_by_id(results_list, obj_id):
    return next((obj for obj in results_list if obj["id"] == str(obj_id)), None)
