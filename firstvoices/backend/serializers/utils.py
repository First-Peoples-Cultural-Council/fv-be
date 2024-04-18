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


def validate_required_headers(input_headers):
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


def validate_all_headers(input_headers):
    logger = logging.getLogger(__name__)
    # If any invalid headers are present, raise a warning
    # If any headers are present in the _n variaiton, but their original header is not present in the list
    # before the variation, raise a warning
    # The headers for which the warning has been raise would be ignored while processing

    input_headers = [h.strip().lower() for h in input_headers]

    valid_headers_present = {s: False for s in VALID_HEADERS}

    for input_header in input_headers:
        if input_header in VALID_HEADERS:
            valid_headers_present[input_header] = True
        else:
            checked = False
            for valid_header in VALID_HEADERS:
                if input_header.startswith(valid_header + "_"):
                    if valid_headers_present[valid_header]:
                        # Check if the original header is present before the variation
                        pass
                    else:
                        logger.warning(
                            f"Warning: Original header not found, instead found just a variation. {input_header}"
                        )
                    checked = True
                    break
            if not checked:
                logger.warning(f"Warning: Unknown header {input_header}")
    return True
