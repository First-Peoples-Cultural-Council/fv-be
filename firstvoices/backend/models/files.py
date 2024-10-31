import datetime
import posixpath

import magic
from django.db import NotSupportedError, models
from django.utils.translation import gettext as _

from backend.permissions import predicates

from .base import BaseSiteContentModel
from .constants import MAX_FILEFIELD_LENGTH
from .import_jobs import ImportJob


def file_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<site slug>/<datestamp>/<filename>
    site_slug = instance.site.slug
    dir_name = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    filename = posixpath.join(site_slug, dir_name, filename)
    return filename


class FileBase(BaseSiteContentModel):
    class Meta:
        abstract = True

    content = models.FileField(
        upload_to=file_directory_path, max_length=MAX_FILEFIELD_LENGTH
    )
    mimetype = models.CharField(blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)
    import_job = models.ForeignKey(
        ImportJob,
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"{self.content.name} ({self.site})"

    def save(self, update_file_metadata=False, **kwargs):
        if not self._state.adding and not update_file_metadata:
            raise NotSupportedError(
                "Editing existing files is not supported at this time. Please create a new file if you would like to "
                "update a media file."
            )

        """
        Sets mimetype and size based on the file contents
        """
        with self.content.file.open(mode="rb") as fb:
            self.mimetype = magic.from_buffer(fb.read(2048), mime=True)
            self.size = self.content.size
            super().save(**kwargs)

    def delete(self, using=None, keep_parents=False):
        """
        Deletes the associated files when the instance is deleted, to prevent orphans.
        """
        result = super().delete(using, keep_parents)
        try:
            self.content.delete(save=False)
        except Exception as e:
            # this will only happen for connection or permission errors, so it's a warning
            self.logger.warning(
                f"Failed to delete file from S3 when deleting [{str(self)}]. Error: {e} "
            )

        return result


class File(FileBase):
    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_at_least_assistant_or_super,
            "change": predicates.is_at_least_assistant_or_super,
            "delete": predicates.can_delete_media,
        }
