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
    return [{"text": entry, "id": str(uuid.uuid4())} for entry in entries]


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


def to_camel_case(snake_str):
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


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


class BatchRelatedMediaMixin:

    @staticmethod
    def assert_maximum_audio_file_data(dictionary_entry, entry_prefix):
        assert dictionary_entry.related_audio.count() == 10
        audio_filenames = dictionary_entry.related_audio.values_list(
            "original__content", flat=True
        )
        for i in range(1, 11):
            assert any(
                f"{entry_prefix}_filename-{i}.mp3" in filename
                for filename in audio_filenames
            )
        audio_titles = dictionary_entry.related_audio.values_list("title", flat=True)
        for i in range(1, 11):
            assert f"{entry_prefix}_title-{i}" in audio_titles
        audio_descriptions = dictionary_entry.related_audio.values_list(
            "description", flat=True
        )
        for i in range(1, 11):
            assert f"{entry_prefix}_description-{i}" in audio_descriptions
        audio_acknowledgements = dictionary_entry.related_audio.values_list(
            "acknowledgement", flat=True
        )
        for i in range(1, 11):
            assert f"{entry_prefix}_acknowledgement-{i}" in audio_acknowledgements
        for audio in dictionary_entry.related_audio.all():
            assert audio.exclude_from_kids is True
            assert audio.exclude_from_games is True
            assert audio.speakers.count() == 10

    @staticmethod
    def assert_maximum_document_file_data(dictionary_entry, entry_prefix):
        assert dictionary_entry.related_documents.count() == 10
        document_filenames = dictionary_entry.related_documents.values_list(
            "original__content", flat=True
        )
        for i in range(1, 11):
            assert any(
                f"{entry_prefix}_filename-{i}.pdf" in filename
                for filename in document_filenames
            )
        document_titles = dictionary_entry.related_documents.values_list(
            "title", flat=True
        )
        for i in range(1, 11):
            assert f"{entry_prefix}_title-{i}" in document_titles
        document_descriptions = dictionary_entry.related_documents.values_list(
            "description", flat=True
        )
        for i in range(1, 11):
            assert f"{entry_prefix}_description-{i}" in document_descriptions
        document_acknowledgements = dictionary_entry.related_documents.values_list(
            "acknowledgement", flat=True
        )
        for i in range(1, 11):
            assert f"{entry_prefix}_acknowledgement-{i}" in document_acknowledgements
        for document in dictionary_entry.related_documents.all():
            assert document.exclude_from_kids is True

    @staticmethod
    def assert_maximum_image_file_data(dictionary_entry, entry_prefix):
        assert dictionary_entry.related_images.count() == 10
        image_filenames = dictionary_entry.related_images.values_list(
            "original__content", flat=True
        )
        for i in range(1, 11):
            assert any(
                f"{entry_prefix}_filename-{i}.jpg" in filename
                for filename in image_filenames
            )
        image_titles = dictionary_entry.related_images.values_list("title", flat=True)
        for i in range(1, 11):
            assert f"{entry_prefix}_title-{i}" in image_titles
        image_descriptions = dictionary_entry.related_images.values_list(
            "description", flat=True
        )
        for i in range(1, 11):
            assert f"{entry_prefix}_description-{i}" in image_descriptions
        image_acknowledgements = dictionary_entry.related_images.values_list(
            "acknowledgement", flat=True
        )
        for i in range(1, 11):
            assert f"{entry_prefix}_acknowledgement-{i}" in image_acknowledgements
        for image in dictionary_entry.related_images.all():
            assert image.exclude_from_kids is True

    @staticmethod
    def assert_maximum_video_file_data(dictionary_entry, entry_prefix):
        assert dictionary_entry.related_videos.count() == 10
        video_filenames = dictionary_entry.related_videos.values_list(
            "original__content", flat=True
        )
        for i in range(1, 11):
            assert any(
                f"{entry_prefix}_filename-{i}.mp4" in filename
                for filename in video_filenames
            )
        video_titles = dictionary_entry.related_videos.values_list("title", flat=True)
        for i in range(1, 11):
            assert f"{entry_prefix}_title-{i}" in video_titles
        video_descriptions = dictionary_entry.related_videos.values_list(
            "description", flat=True
        )
        for i in range(1, 11):
            assert f"{entry_prefix}_description-{i}" in video_descriptions
        video_acknowledgements = dictionary_entry.related_videos.values_list(
            "acknowledgement", flat=True
        )
        for i in range(1, 11):
            assert f"{entry_prefix}_acknowledgement-{i}" in video_acknowledgements
        for video in dictionary_entry.related_videos.all():
            assert video.exclude_from_kids is True

    @staticmethod
    def get_maximum_valid_related_media_columns():
        expected_valid_columns = ["title", "type"]
        media_prefixes = ["audio", "document", "img", "video"]
        media_suffixes = [
            "filename",
            "title",
            "description",
            "acknowledgement",
            "include_in_kids_site",
        ]

        for prefix in media_prefixes:
            for suffix in media_suffixes:
                expected_valid_columns.append(f"{prefix}_{suffix}")

                for i in range(2, 11):
                    expected_valid_columns.append(f"{prefix}_{i}_{suffix}")

        for i in range(1, 11):
            if i == 1:
                expected_valid_columns.append("audio_include_in_games")
            else:
                expected_valid_columns.append(f"audio_{i}_include_in_games")

            for j in range(1, 11):
                if i == 1 and j == 1:
                    expected_valid_columns.append("audio_speaker")
                elif i == 1:
                    expected_valid_columns.append(f"audio_speaker_{j}")
                elif j == 1:
                    expected_valid_columns.append(f"audio_{i}_speaker")
                else:
                    expected_valid_columns.append(f"audio_{i}_speaker_{j}")

        return expected_valid_columns

    def upload_multiple_media_files(self, count, filename, file_type, import_job):
        if file_type == "audio":
            base_file = "sample-audio.mp3"
            file_ext = ".mp3"
            media_factory = factories.FileFactory
            mimetype = "audio/mpeg"
        elif file_type == "image":
            base_file = "sample-image.jpg"
            file_ext = ".jpg"
            media_factory = factories.ImageFileFactory
            mimetype = "image/jpeg"
        elif file_type == "video":
            base_file = "video_example_small.mp4"
            file_ext = ".mp4"
            media_factory = factories.VideoFileFactory
            mimetype = "video/mp4"
        elif file_type == "document":
            base_file = "sample-document.pdf"
            file_ext = ".pdf"
            media_factory = factories.FileFactory
            mimetype = "application/pdf"
        else:
            return
        for x in range(1, count + 1):
            media_factory(
                site=self.site,
                content=get_sample_file(
                    filename=f"{base_file}",
                    mimetype=mimetype,
                    title=f"{filename}-{x}{file_ext}",
                ),
                import_job=import_job,
            )
