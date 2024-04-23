import logging

from rest_framework import serializers
from rest_framework.exceptions import APIException

from backend.models.sites import Site

# For import-jobs header validation
REQUIRED_HEADERS = ["title", "type"]
VALID_HEADERS = [
    "title",
    "type",
    "translation",
    "audio",
    "image",
    "video",
    "video_embed_link",
    "category",
    "note",
    "acknowledgement",
    "part_of_speech",
    "pronunciation",
    "alt_spelling",
    "visibility",
    "include_on_kids_site",
    "include_in_games",
    "related_entry",
]


def get_site_from_context(serializer):
    logger = logging.getLogger(__name__)

    if "site" in serializer.context:
        return serializer.context["site"]
    elif "site_slug" in serializer.context:
        site = Site.objects.filter(slug=serializer.context["site_slug"])
        if len(site) == 0:
            logger.error(
                "get_site_from_context - "
                "Tried to retrieve site from context but no site found for the slug provided."
            )
            raise APIException
        return site.first()
    else:
        logger.error(
            "get_site_from_context - Failed to retrieve site information from the context. "
            "The required 'site' or 'site_slug' parameters were not found in the serializer context"
        )
        raise APIException


def get_story_from_context(serializer):
    logger = logging.getLogger(__name__)

    if "story" in serializer.context:
        return serializer.context["story"]
    else:
        logger.error(
            "get_story_from_context - Failed to retrieve story id from the context. "
            "The required 'story' property was not found in the serializer context"
        )
        raise APIException


def get_usages_total(usages_dict):
    # Get total count of all objects a media file is used in
    total = 0
    for usage in usages_dict.values():
        if isinstance(
            usage, list
        ):  # adding a check as some keys contain objects and not arrays
            total += len(usage)
        elif isinstance(usage, dict) and "id" in usage:
            # If there is a site the image is a banner/logo of
            total += 1
    return total


def check_required_headers(input_headers):
    # check for the required headers

    input_headers = [h.strip().lower() for h in input_headers]
    if set(REQUIRED_HEADERS) - set(input_headers):
        raise serializers.ValidationError(
            detail={
                "data": [
                    "CSV file does not have the required headers. Please check and upload again."
                ]
            }
        )
    return True


def validate_headers(input_headers):
    input_headers = [h.strip().lower() for h in input_headers]

    # If any invalid headers are present, skip them and raise a warning
    for header in input_headers:
        if header in VALID_HEADERS:
            continue
        else:
            check_header_variation(header)


def check_header_variation(input_header):
    # The input header can have a _n variation upto 5, e.g. note_5
    # raise a warning if the header is not valid or n>5.

    logger = logging.getLogger(__name__)
    splits = input_header.split("_")
    if len(splits) >= 2:
        prefix = "_".join(splits[:-1])
        variation = splits[-1]
    else:
        prefix = input_header
        variation = None

    # Check if the prefix is a valid header
    if prefix in VALID_HEADERS and variation and variation.isdigit():
        variation = int(variation)
        if variation < 1 or variation > 5:
            logger.warning(f"Variation out of range. Skipping column {input_header}.")
            return

    logger.warning(f"Unknown header. Skipping column {input_header}.")
