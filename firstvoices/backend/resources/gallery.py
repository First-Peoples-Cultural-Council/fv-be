import logging

from django.core.exceptions import ValidationError
from import_export import fields

from backend.models import Gallery, GalleryItem, Image
from backend.resources.base import SiteContentResource


class GalleryResource(SiteContentResource):
    description = fields.Field(column_name="description", attribute="introduction")

    # Save related image data for GalleryItems
    related_images = fields.Field(
        column_name="related_images",
    )

    def after_import_row(self, row, row_result, **kwargs):
        logger = logging.getLogger(__name__)

        # After importing the Gallery, handle GalleryItems
        if row_result.import_type in ["new", "update"]:
            related_images = row.get("related_images", "")
            image_ids = [
                img_id.strip() for img_id in related_images.split(",") if img_id.strip()
            ]

            try:
                gallery = Gallery.objects.get(id=row_result.object_id)
            except Gallery.DoesNotExist:
                row_result.errors.append(
                    ValidationError(
                        f"Gallery with id {row_result.object_id} not found. "
                        f"This is likely due to the Gallery not being imported. "
                        f"Check the result for other errors or validation errors."
                    )
                )
                return  # Exit early if the Gallery is not found

            for order, image_id in enumerate(image_ids):
                try:
                    image = Image.objects.get(id=image_id)
                    GalleryItem.objects.create(
                        gallery=gallery,
                        image=image,
                        ordering=order,
                    )
                except Image.DoesNotExist:
                    logger.warning(
                        f"Image with id {image_id} not found. Skipping GalleryItem creation."
                    )
                    continue

    class Meta:
        model = Gallery
        clean_model_instances = True
