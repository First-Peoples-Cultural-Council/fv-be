import json
from os import path

from firstvoices.backend.models.category import Category


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
        c.is_cleaned = False
        c.save()
