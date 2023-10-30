from django.core.cache import caches
import logging

from django.db.models import Prefetch
from rest_framework.throttling import UserRateThrottle

from backend.models import AppJson
from backend.models.media import Audio, Image, Video


def get_select_related_media_fields(media_field_name):
    """
    Args:
        media_field_name: the name of an Image or Video model field. To get the fields for an Image or Video model,
            set media_field_name as None

    Returns:
        a list of field name strings including the provided media field and its associated file models

    """
    f = f"{media_field_name}__" if media_field_name else ""
    fields = [f"{f}original", f"{f}thumbnail", f"{f}small", f"{f}medium"]
    if media_field_name:
        fields = fields + [media_field_name]
    fields.append(f"{f}site")
    return fields


def get_media_prefetch_list(user):
    return [
        Prefetch(
            "related_audio",
            queryset=Audio.objects.visible(user)
            .select_related("original", "site")
            .prefetch_related("speakers"),
        ),
        Prefetch(
            "related_images",
            queryset=Image.objects.visible(user).select_related(
                *get_select_related_media_fields(None)
            ),
        ),
        Prefetch(
            "related_videos",
            queryset=Video.objects.visible(user).select_related(
                *get_select_related_media_fields(None)
            ),
        ),
    ]


def get_site_url_from_appjson(site):
    logger = logging.getLogger(__name__)
    base_url = AppJson.objects.filter(key="frontend_base_url")
    if base_url.count() > 0:
        return base_url[0].json + "/" + site.slug + "/"
    else:
        logger.warning(
            'No AppJson instance with key "frontend_base_url" found. Site URLs will not be included in join request '
            'emails. Please add a key "frontend_base_url" to AppJson with the base URL of the frontend as the value '
            'string (eg: "https://firstvoices.com").'
        )
        return None


class CustomUserRateThrottle(UserRateThrottle):
    cache = caches["throttle"]


class BurstRateThrottle(CustomUserRateThrottle):
    scope = "burst"


class SustainedRateThrottle(CustomUserRateThrottle):
    scope = "sustained"
