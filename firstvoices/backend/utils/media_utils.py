from django.core.exceptions import ObjectDoesNotExist

from backend.models.media import Image, Video
from backend.models.sites import Site


def verify_media_source(site_slug, media_type, media_id):
    if media_type == "image":
        media = Image.objects.filter(id=media_id)
    elif media_type == "video":
        media = Video.objects.filter(id=media_id)

    if len(media) == 0:
        raise ObjectDoesNotExist

    site = Site.objects.filter(slug=site_slug)
    if len(site) == 0:
        raise ObjectDoesNotExist

    if media[0].site_id == site[0].id:
        return True

    return False
