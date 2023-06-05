import sys
from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from django.db import models
from django.utils.translation import gettext as _
from PIL import Image as PILImage

from backend.permissions import predicates

from .base import AudienceMixin, BaseSiteContentModel


class Person(BaseSiteContentModel):
    # from FVContributor

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_edit_core_uncontrolled_data,
        }

    # from dc:title
    name = models.CharField(max_length=200)

    # from FVContributor dc:description
    bio = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.name} ({self.site})"


def media_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<site slug>/<filename>
    return f"{instance.site.slug}/{filename}"


class MediaBase(AudienceMixin, BaseSiteContentModel):
    class Meta:
        abstract = True

    # see specific media models for migration info
    acknowledgement = models.TextField(max_length=500, blank=True)

    # from dc:title
    title = models.CharField(max_length=200)

    # from dc:description
    description = models.CharField(max_length=500, blank=True)

    # exclude_from_games from fv-word:available_in_games, fvaudience:games

    # exclude_from_kids from fvaudience:children fvm:child_focused

    # from fvm:shared
    is_shared = models.BooleanField(default=False)

    # from fvm:content
    content = models.FileField(upload_to=media_directory_path)

    def delete(self, using=None, keep_parents=False):
        """
        Deletes the associated media files when the instance is deleted, to prevent orphans.
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


class Audio(MediaBase):
    # from fvaudio

    class Meta:
        verbose_name = _("Audio")
        verbose_name_plural = _("Audio")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # acknowledgment from fvm:recorder
    # from fvm:source
    speakers = models.ManyToManyField(
        Person, through="AudioSpeaker", related_name="audio_set", blank=True
    )

    def __str__(self):
        return f"{self.title} / {self.site} (Audio)"


class AudioSpeaker(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Audio Speaker")
        verbose_name_plural = _("Audio Speakers")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    audio = models.ForeignKey(
        Audio, on_delete=models.CASCADE, related_name="audiospeaker_set"
    )
    speaker = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="audiospeaker_set"
    )

    def __str__(self):
        return f"Audio Speaker {self.audio.title} - ({self.speaker.name})"


def get_output_image_size(max_size, input_width, input_height):
    """
    Returns the output image size given a max size to scale the image to. The largest dimension of the input image is
    scaled down to the max size setting and the other dimension is scaled down, keeping the original aspect ratio.
    The original size is used if the input image is smaller in both dimensions than the max size.

    :param max_size: The maximum size (width or height) of the output image.
    :param input_width: The input image width.
    :param input_height: The input image height.
    :return: The output image size as a tuple (width, height).
    """
    if input_width >= input_height:
        if input_width > max_size:
            return (
                max_size,
                round(input_height / (input_width / max_size)),
            )
    else:
        if input_height > max_size:
            return (
                round(input_width / (input_height / max_size)),
                max_size,
            )
    return input_width, input_height


class Image(MediaBase):
    # from fvpicture

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # acknowledgement from fvm:recorder, fvm:source

    # from fvm:content
    content = models.ImageField(upload_to=media_directory_path)

    thumbnail = models.ImageField(upload_to=media_directory_path, blank=True)
    small = models.ImageField(upload_to=media_directory_path, blank=True)
    medium = models.ImageField(upload_to=media_directory_path, blank=True)

    def __str__(self):
        return f"{self.title} / {self.site} (Image)"

    def generate_resized_images(self):
        """
        A function to generate a set of resized images when an Image model is saved
        """
        for size_name, max_size in settings.IMAGE_SIZES.items():
            output_img = BytesIO()

            img = PILImage.open(self.content)
            image_name = self.content.name.split(".")[0]

            output_size = get_output_image_size(max_size, img.width, img.height)

            img.thumbnail(output_size)
            # Remove transparency values if they exist so that the image can be converted to JPEG.
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_img, format="JPEG", quality=90)

            # Set the model field to the newly generated image.
            setattr(
                self,
                size_name,
                InMemoryUploadedFile(
                    output_img,
                    "ImageField",
                    f"{image_name}_{size_name}.jpg",
                    "image/jpeg",
                    sys.getsizeof(output_img),
                    None,
                ),
            )

    def save(self, **kwargs):
        # Boolean which returns True if the image is new, otherwise false.
        is_new = self._state.adding is True
        # Boolean which returns True if the image file has been updated, otherwise false (returns true for a new image).
        content_updated = hasattr(self.content, "file") and isinstance(
            self.content.file, UploadedFile
        )

        # If the main image file was updated then delete the old image files from AWS
        if content_updated and not is_new:
            try:
                old_image = Image.objects.get(pk=self.pk)
                old_image.content.delete(save=False)
                self.thumbnail.delete(save=False)
                self.small.delete(save=False)
                self.medium.delete(save=False)
            except Exception as e:
                # this will only happen for connection or permission errors, so it's a warning
                self.logger.warn(
                    f"Failed to delete file from S3 when deleting [{str(self)}]. Error: {e} "
                )

        # If the image is new or the file has been updated then generate new resized images
        if is_new or content_updated:
            self.generate_resized_images()

        super().save()

    def delete(self, using=None, keep_parents=False):
        """
        Deletes the associated media files when the instance is deleted, to prevent orphans.
        """
        result = super().delete(using, keep_parents)
        try:
            self.thumbnail.delete(save=False)
            self.small.delete(save=False)
            self.medium.delete(save=False)
        except Exception as e:
            # this will only happen for connection or permission errors, so it's a warning
            self.logger.warn(
                f"Failed to delete file from S3 when deleting [{str(self)}]. Error: {e} "
            )

        return result


class Video(MediaBase):
    # from fvvideo

    class Meta:
        verbose_name = _("Video")
        verbose_name_plural = _("Videos")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # acknowledgement from fvm:recorder, fvm:source

    def __str__(self):
        return f"{self.title} / {self.site} (Video)"


class RelatedMediaMixin(models.Model):
    """
    Related media fields with standard names.
    """

    class Meta:
        abstract = True

    related_audio = models.ManyToManyField(Audio, blank=True)
    related_images = models.ManyToManyField(Image, blank=True)
    related_videos = models.ManyToManyField(Video, blank=True)
