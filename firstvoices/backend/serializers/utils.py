import logging

from rest_framework.exceptions import APIException

from backend.models.sites import Site


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
        elif hasattr(usage, "id"):
            # If there is a site the image is a banner/logo of
            total += 1
    return total
