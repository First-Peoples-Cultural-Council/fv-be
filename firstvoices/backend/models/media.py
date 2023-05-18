from django.db import models

from .base import BaseSiteContentModel


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<site slug>/<filename>
    return f"{instance.site.slug}/{filename}"


class Image(BaseSiteContentModel):
    """
    Stub
    """

    # from fvpicture

    # from dc:title
    title = models.CharField(max_length=200)

    # organizes file uploads into site folders. Could also add a subfolder for each media type (/site/images/file.jpg)
    # from fvm:content, see fw-4352 for migration details
    content = models.ImageField(upload_to=user_directory_path)

    def delete(self, using=None, keep_parents=False):
        """
        Deletes the associated media file when the instance is deleted, to prevent orphans.
        """
        result = super().delete(using, keep_parents)
        try:
            self.content.delete(save=False)
        except Exception as e:
            # this will only happen for connection or permission errors, so it's a warning
            self.logger.warn(
                f"Failed to delete file from S3 when deleting [{str(self)}]. Error: {e} "
            )

        return result
