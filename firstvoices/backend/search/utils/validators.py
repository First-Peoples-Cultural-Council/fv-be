from django.core import exceptions
from django.utils.translation import gettext as _
from rest_framework import serializers

from backend.models.constants import Visibility
from backend.search.utils.constants import LENGTH_FILTER_MAX, VALID_DOCUMENT_TYPES
from backend.search.utils.query_builder_utils import SearchDomains


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


def get_valid_document_types(input_types, allowed_values=VALID_DOCUMENT_TYPES):
    if not input_types:
        return allowed_values

    values = input_types.split(",")
    selected_values = []

    for value in values:
        stripped_value = value.strip().lower()
        if stripped_value in allowed_values and stripped_value not in selected_values:
            selected_values.append(stripped_value)

    if len(selected_values) == 0:
        return None

    return selected_values


def get_valid_domain(input_domain_str):
    string_lower = input_domain_str.strip().lower()

    if not string_lower:
        return "both"

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


def get_valid_category_id(site, input_category):
    # If input_category is empty, category filter should not be added
    if input_category:
        try:
            # If category does not belong to the site specified, return empty result set
            valid_category = site.category_set.filter(id=input_category)
            if len(valid_category):
                return valid_category[0].id
        except exceptions.ValidationError:
            return None

    return None


def get_valid_import_job_id(site, import_job_input_str):
    # If import_job_input_str is empty, filter should not be added
    if import_job_input_str:
        try:
            # If import-job does not belong to the site specified, return empty result set
            valid_import_job = site.importjob_set.filter(id=import_job_input_str)
            if len(valid_import_job):
                return valid_import_job[0].id
        except exceptions.ValidationError:
            return None

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


def get_valid_visibility(input_visibility_str):
    if not input_visibility_str:
        return ""

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


def get_valid_site_feature(input_site_feature_str):
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
