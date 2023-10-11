import json
from os import path

from backend.models.category import Category
from backend.models.widget import SiteWidget

# constants for the default widgets, subset of the complete list of widgets
WIDGET_ALPHABET = "WIDGET_ALPHABET"
WIDGET_STATS = "WIDGET_STATS"
WIDGET_WOTD = "WIDGET_WOTD"


def load_data(json_file):
    """Helper function to load data from a json file."""

    with open(path.dirname(__file__) + "/" + json_file, encoding="utf-8") as data_file:
        json_data = json.loads(data_file.read())
        return json_data


def load_default_categories(site):
    """
    Function to load default categories on the creation of a new site. Used in the save function of the site
    model.
    """

    # Load the default categories from file.
    default_categories = load_data("default_categories.json")

    # Get a list of parent categories
    parent_categories = [
        category
        for category in default_categories
        if category["fields"]["parent"] == ""
    ]

    # Get a list of child categories
    child_categories = [
        category
        for category in default_categories
        if category["fields"]["parent"] != ""
    ]

    # Create the categories for the new model
    # Adds the parent categories first since the children depend on them
    for category in parent_categories + child_categories:
        fields = category["fields"]

        # If the current category getting added has a parent, grab it from the existing categories.
        if fields["parent"] != "":
            parent_category = Category.objects.filter(
                site_id=site.id, title=fields["parent"]
            )[0]
        else:
            parent_category = None

        # Create and save the category
        c = Category(
            title=fields["title"],
            site=site,
            parent=parent_category,
            created_by=site.created_by,
            last_modified_by=site.last_modified_by,
        )
        c.save()


def load_default_widgets(site):
    """
    Function to add a set of default widgets to any new site.
    """

    # list of default widgets
    default_widgets = [
        {"type": WIDGET_ALPHABET, "title": "alphabet"},
        {"type": WIDGET_STATS, "title": "new-this-week-statistics"},
        {"type": WIDGET_WOTD, "title": "word-of-the-day"},
    ]

    for widget in default_widgets:
        new_widget = SiteWidget.objects.create(
            site=site,
            widget_type=widget["type"],
            title=widget["title"],
            visibility=site.visibility,
        )
        new_widget.save()
