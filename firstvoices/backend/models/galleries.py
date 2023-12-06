from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext as _

from backend.models import Image
from backend.models.base import (
    BaseModel,
    BaseSiteContentModel,
    TranslatedIntroMixin,
    TranslatedTitleMixin,
)
from backend.permissions import predicates


class Gallery(TranslatedTitleMixin, TranslatedIntroMixin, BaseSiteContentModel):
    """
    Represents a gallery of images on a language site.
    """

    class Meta:
        verbose_name = _("gallery")
        verbose_name_plural = _("galleries")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_delete_core_uncontrolled_data,
        }

    cover_image = models.OneToOneField(
        Image,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="gallery_cover_image",
    )

    def __str__(self):
        return self.title


class GalleryImage(BaseModel):
    """
    Represents an image in a gallery.
    """

    class Meta:
        verbose_name = _("gallery image")
        verbose_name_plural = _("gallery images")
        constraints = [
            models.UniqueConstraint(
                fields=["gallery", "image"],
                name="unique_gallery_image",
            ),
            models.UniqueConstraint(
                fields=["gallery", "order"],
                name="unique_gallery_image_order",
            ),
        ]
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_delete_core_uncontrolled_data,
        }
        indexes = [
            models.Index(fields=["gallery", "order"], name="gallery_image_order_idx"),
        ]

    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )

    order = models.SmallIntegerField(
        validators=[MinValueValidator(0)], null=False, default=0
    )

    def __str__(self):
        return self.image.title
