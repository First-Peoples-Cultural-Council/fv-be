from django.core import exceptions
from django.utils.translation import gettext as _
from rest_framework import serializers

from backend.models import Site
from backend.models.constants import Visibility
from backend.models.dictionary import ExternalDictionaryEntrySystem
from backend.search.constants import ALL_SEARCH_TYPES, LENGTH_FILTER_MAX
from backend.search.queries.query_builder_utils import SearchDomains


def get_valid_count(count, property_name):
    exception_message = _("Value must be a non-negative integer.")
    max_value = LENGTH_FILTER_MAX

    # If empty, return
    if count is None:
        return count

    try:
        count = int(count)
    except ValueError:
        # If a non integer value is passed, raise Exception
        raise serializers.ValidationError({property_name: [exception_message]})

    if count < 0:
        raise serializers.ValidationError({property_name: [exception_message]})

    # If a number is supplied greater than the max value, consider max value
    if count > max_value:
        count = max_value

    return count


def get_valid_search_types(input_types, default_value=ALL_SEARCH_TYPES):
    if input_types is None or input_types == "":
        return default_value

    values = input_types.split(",")
    selected_values = []

    for value in values:
        stripped_value = value.strip().lower()
        if stripped_value in ALL_SEARCH_TYPES and stripped_value not in selected_values:
            selected_values.append(stripped_value)

    if len(selected_values) == 0:
        return None

    return selected_values


def get_valid_domain(input_domain_str, default_value="both"):
    string_lower = input_domain_str.strip().lower()

    if not string_lower:
        return default_value

    if (
        string_lower == SearchDomains.BOTH.value
        or string_lower == SearchDomains.LANGUAGE.value
        or string_lower == SearchDomains.TRANSLATION.value
    ):
        return string_lower
    else:  # if invalid string is passed
        return None


def get_valid_starts_with_char(input_str):
    # Starting alphabet can be a combination of characters as well
    # taking only first word if multiple words are supplied
    valid_str = str(input_str).strip().split(" ")[0]
    return valid_str


def get_valid_instance_id(site, model, instance_id):
    if not instance_id:
        return None

    try:
        valid_instance = model.objects.filter(site=site, id=instance_id)
        return valid_instance[0].id
    except (exceptions.ValidationError, IndexError):
        # invalid uuid or no entry found with provided id
        return None


def get_valid_boolean(input_val):
    # Python treats bool("False") as true, thus manual verification
    cleaned_input = str(input_val).strip().lower()

    if cleaned_input == "true":
        return True
    elif cleaned_input == "false":
        return False
    else:
        return None


def get_valid_visibility(input_visibility_str, default_value=""):
    if not input_visibility_str:
        return default_value

    input_visibility = input_visibility_str.split(",")
    selected_values = []

    for value in input_visibility:
        string_upper = value.strip().upper()
        if (
            string_upper == Visibility.TEAM.label.upper()
            or string_upper == Visibility.MEMBERS.label.upper()
            or string_upper == Visibility.PUBLIC.label.upper()
        ) and Visibility[string_upper] not in selected_values:
            selected_values.append(Visibility[string_upper])

    if len(selected_values) == 0:
        return None
    return selected_values


def get_valid_sort(input_sort_by_str):
    input_string = input_sort_by_str.lower().strip().split("_")

    descending = len(input_string) > 1 and input_string[1] == "desc"

    if len(input_string) > 0 and (
        input_string[0] == "created"
        or input_string[0] == "modified"
        or input_string[0] == "title"
        or input_string[0] == "random"
    ):
        return input_string[0], descending
    else:  # if invalid string is passed
        return None, None


def get_valid_site_features(input_site_feature_str):
    if not input_site_feature_str:
        return None

    input_site_feature = input_site_feature_str.split(",")
    selected_values = []

    for value in input_site_feature:
        cleaned_value = value.strip().lower()
        if cleaned_value not in selected_values:
            selected_values.append(cleaned_value)

    if len(selected_values) == 0:
        return None
    return selected_values


def get_valid_site_ids_from_slugs(input_site_slug_str, user):
    if not input_site_slug_str:
        return ""

    input_site_slugs = [
        value.strip().lower() for value in input_site_slug_str.split(",")
    ]
    selected_values = list(
        Site.objects.visible(user)
        .filter(slug__in=input_site_slugs)
        .values_list("id", flat=True)
    )

    if len(selected_values) == 0:
        return None
    return selected_values


def get_valid_external_system_id(title):
    if not title:
        return None

    try:
        valid_instance = ExternalDictionaryEntrySystem.objects.filter(title=title)
        return str(valid_instance[0].id)
    except (exceptions.ValidationError, IndexError):
        # invalid title or no entry found with provided title
        return None
