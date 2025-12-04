import logging
import os
import random
import string
import sys
import uuid
from contextlib import contextmanager

import pytest
import tablib
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import DEFAULT_DB_ALIAS, connections

from backend.models.constants import Visibility
from backend.models.widget import SiteWidgetListOrder
from backend.tests import factories


def assert_list(expected_list, actual_list):
    assert len(expected_list) == len(actual_list)

    for i, item in enumerate(expected_list):
        assert item in actual_list


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
    widget_one_one = widget_list_one.widgets.order_by("title").all()[0]
    widget_one_two = widget_list_one.widgets.order_by("title").all()[1]
    widget_one_three = widget_list_one.widgets.order_by("title").all()[2]
    widget_two_one = widget_list_two.widgets.order_by("title").all()[0]
    widget_two_two = widget_list_two.widgets.order_by("title").all()[1]
    widget_two_three = widget_list_two.widgets.order_by("title").all()[2]

    widgets = [
        widget_one_one,
        widget_one_two,
        widget_one_three,
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


def equate_list_content_without_order(actual, expected):
    difference = set(actual) ^ set(expected)
    return not difference


@contextmanager
def not_raises(exception):
    try:
        yield
    except exception:
        raise pytest.fail(f"Did raise {exception}")


def get_sample_file(filename, mimetype, file_dir="factories/resources", title=None):
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_dir, filename)
    file = open(path, "rb")
    return InMemoryUploadedFile(
        file,
        "FileField",
        title if title is not None else filename,
        mimetype,
        sys.getsizeof(file),
        None,
    )


def format_dictionary_entry_related_field(entries):
    # To format the provided ArrayField to expected API response structure
    return [{"text": entry} for entry in entries]


def is_valid_uuid(uuid_string):
    try:
        val = uuid.UUID(uuid_string)
    except ValueError:
        return False
    return str(val) == uuid_string


def get_batch_import_test_dataset(filename):
    path = (
        os.path.dirname(os.path.realpath(__file__))
        + f"/factories/resources/import_job/{filename}"
    )
    file = open(path, "rb").read().decode("utf-8-sig")
    data = tablib.Dataset().load(file, format="csv")
    return data


class TransactionOnCommitMixin:
    @classmethod
    @contextmanager
    def capture_on_commit_callbacks(cls, *, using=DEFAULT_DB_ALIAS, execute=False):
        """Context manager to capture transaction.on_commit() callbacks."""
        callbacks = []
        commit_handlers = connections[using].run_on_commit
        start_count = len(commit_handlers)
        try:
            yield callbacks
        finally:
            while True:
                callback_count = len(commit_handlers)
                for _, callback, robust in commit_handlers[start_count:]:
                    callbacks.append(callback)
                    if execute:
                        cls._execute_callback(callback, robust)

                if callback_count == len(commit_handlers):
                    break
                start_count = callback_count

    @classmethod
    def _execute_callback(cls, callback, robust):
        if robust:
            try:
                callback()
            except Exception as e:
                logging.error(
                    f"Error calling {callback.__qualname__} in on_commit() (%s).",
                    e,
                    exc_info=True,
                )
        else:
            callback()
