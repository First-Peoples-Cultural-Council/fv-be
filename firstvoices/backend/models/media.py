from django.db import models

from .base import BaseSiteContentModel


class Image(BaseSiteContentModel):
    """
    Stub
    """

    # from fvpicture

    # from dc:title
    title = models.CharField(max_length=200)

    # from fvm:content, see fw-4352 for migration details
    content = models.ImageField()
