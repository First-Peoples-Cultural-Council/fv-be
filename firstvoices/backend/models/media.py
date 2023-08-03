import datetime
import os.path
import posixpath
import sys
import tempfile
from io import BytesIO

import ffmpeg
import magic
import rules
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import NotSupportedError, models
from django.utils.translation import gettext as _
from embed_video.fields import EmbedVideoField
from PIL import Image as PILImage

from backend.permissions import predicates

from .base import AudienceMixin, BaseModel, BaseSiteContentModel


class Person(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_delete_core_uncontrolled_data,
        }

    name = models.CharField(max_length=200)

    bio = models.CharField(max_length=500, blank=True, null=False)

    def __str__(self):
        return f"{self.name} ({self.site})"


def media_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/<site slug>/<datestamp>/<filename>
    site_slug = instance.site.slug
    dirname = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
    filename = posixpath.join(site_slug, dirname, filename)
    return filename


class FileBase(BaseSiteContentModel):
    class Meta:
        abstract = True

    content = models.FileField(upload_to=media_directory_path)
    mimetype = models.CharField(blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.content.name} ({self.site})"

    def save(self, **kwargs):
        if not self._state.adding:
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
            self.logger.warn(
                f"Failed to delete file from S3 when deleting [{str(self)}]. Error: {e} "
            )

        return result


class File(FileBase):
    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_delete_core_uncontrolled_data,
        }


class VisualFileBase(FileBase):
    """A File model with additional height and width properties"""

    class Meta:
        abstract = True

    height = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)


class ImageFile(VisualFileBase):
    content = models.ImageField(
        upload_to=media_directory_path, height_field="height", width_field="width"
    )

    class Meta:
        verbose_name = _("Image File")
        verbose_name_plural = _("Image Files")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_delete_core_uncontrolled_data,
        }


def get_local_video_file(original):
    input_extension = "." + original.name.split(".")[1]
    temp_file = tempfile.NamedTemporaryFile(suffix=input_extension)
    original.file.seek(0)
    image_file = original.file.read()
    temp_file.write(image_file)
    return temp_file


class VideoFile(VisualFileBase):
    class Meta:
        verbose_name = _("Video File")
        verbose_name_plural = _("Video Files")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_delete_core_uncontrolled_data,
        }

    def save(self, **kwargs):
        try:
            with get_local_video_file(self.content) as temp_file:
                video_info = self.get_video_info(temp_file)

            self.width = int(video_info["width"])
            self.height = int(video_info["height"])

        except ffmpeg.Error as e:
            self.logger.error(
                f"Failed to probe video file using ffmpeg [{self.content.name}]. \n"
                f"Error: {e}\n"
                f"{e.stderr.decode('utf8')}\n"
            )

        super().save(**kwargs)

    def get_video_info(self, temp_file):
        probe = ffmpeg.probe(temp_file.name)
        video_stream = next(
            (stream for stream in probe["streams"] if stream["codec_type"] == "video"),
            None,
        )
        return video_stream


class MediaBase(AudienceMixin, BaseSiteContentModel):
    class Meta:
        abstract = True

    # from fvm:content
    original = models.OneToOneField(File, null=True, on_delete=models.SET_NULL)

    # from dc:title
    title = models.CharField(max_length=200)

    # from dc:description
    description = models.CharField(max_length=500, blank=True)

    # see specific media models for migration info
    acknowledgement = models.TextField(max_length=500, blank=True)

    # exclude_from_games from fv-word:available_in_games, fvaudience:games

    # exclude_from_kids from fvaudience:children fvm:child_focused

    # from fvm:shared
    is_shared = models.BooleanField(default=False)

    def save(self, **kwargs):
        if self._state.adding:
            self._add_media()

        elif self._is_updating_original():
            self._update_media()

        super().save(**kwargs)

    def _is_updating_original(self):
        if self._state.adding:
            return False

        old_instance = self._get_saved_instance()
        is_content_updated = self.original.pk != old_instance.original.pk
        return is_content_updated

    def _add_media(self):
        """
        Subclasses can override to handle tasks associated with adding media. E.g., generating thumbnails.
        """
        pass

    def _update_media(self):
        self._delete_old_media()

    def _delete_old_media(self):
        """
        Deletes the old file model when the "original" field is updated, to prevent orphans.
        """
        old_instance = self._get_saved_instance()
        try:
            self._delete_related_media(old_instance)
        except Exception as e:
            # this will only happen for connection or permission errors, so it's a warning
            self.logger.warn(
                f"Failed to delete associated file model when updating [{str(self)}]. Error: {e} "
            )

    def _get_saved_instance(self):
        return self.__class__.objects.get(pk=self.pk)

    def _delete_related_media(self, instance):
        instance.original.delete()

    def delete(self, using=None, keep_parents=False):
        """
        Deletes the associated file model when the instance is deleted, to prevent orphans.
        """
        result = super().delete(using, keep_parents)
        try:
            self._delete_related_media(self)
        except Exception as e:
            # this will only happen for connection or permission errors, so it's a warning
            self.logger.warn(
                f"Failed to delete associated file model when deleting [{str(self)}]. Error: {e} "
            )

        return result


class Audio(MediaBase):
    # from fvaudio

    class Meta:
        verbose_name = _("Audio")
        verbose_name_plural = _("Audio")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_delete_core_uncontrolled_data,
        }

    # acknowledgment from fvm:recorder

    # from fvm:source
    speakers = models.ManyToManyField(
        Person, through="AudioSpeaker", related_name="audio_set", blank=True
    )

    def __str__(self):
        return f"{self.title} / {self.site} (Audio)"


class AudioSpeaker(BaseModel):
    class Meta:
        verbose_name = _("Audio Speaker")
        verbose_name_plural = _("Audio Speakers")
        rules_permissions = {
            "view": rules.always_allow,  # will be removed with fw-4368
            "add": rules.always_allow,
            "change": rules.always_allow,
            "delete": rules.always_allow,
        }

    audio = models.ForeignKey(
        Audio, on_delete=models.CASCADE, related_name="audiospeaker_set"
    )
    speaker = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="audiospeaker_set"
    )

    def __str__(self):
        return f"Audio Speaker {self.audio.title} - ({self.speaker.name})"


def get_output_dimensions(max_size, input_width, input_height):
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


class ThumbnailMixin(models.Model):
    class Meta:
        abstract = True

    thumbnail = models.OneToOneField(
        ImageFile,
        related_name="%(class)s_thumbnail",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    small = models.OneToOneField(
        ImageFile,
        related_name="%(class)s_small",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    medium = models.OneToOneField(
        ImageFile,
        related_name="%(class)s_medium",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    def generate_resized_images(self):
        """
        A function to generate a set of resized images when the model is saved.
        """
        raise NotImplementedError

    def _add_media(self):
        super()._add_media()
        self.generate_resized_images()

    def _update_media(self):
        super()._update_media()
        self.generate_resized_images()

    def _delete_related_media(self, instance):
        """
        Deletes additional thumbnail models.
        """
        super()._delete_related_media(instance)
        instance.thumbnail.delete()
        instance.small.delete()
        instance.medium.delete()

    def add_image_file(self, file_name, output_img, output_size):
        content = InMemoryUploadedFile(
            file=output_img,
            field_name="ImageField",
            name=file_name,
            content_type="image/jpeg",
            size=sys.getsizeof(output_img),
            charset=None,
        )

        model = ImageFile(
            content=content,
            site=self.site,
            created_by=self.created_by,
            last_modified_by=self.last_modified_by,
        )
        model.save()

        return model


class Image(ThumbnailMixin, MediaBase):
    # from fvpicture

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_delete_core_uncontrolled_data,
        }

    # acknowledgement from fvm:recorder, fvm:source

    # from fvm:content
    original = models.OneToOneField(
        ImageFile, related_name="image", null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.title} / {self.site} (Image)"

    def generate_resized_images(self):
        """
        A function to generate a set of resized images when an Image model is saved
        """
        for size_name, max_size in settings.IMAGE_SIZES.items():
            original = self.original.content
            image_name = original.name.split(".")[0]
            thumbnail_name = f"{image_name}_{size_name}.jpg"

            with PILImage.open(original.file.open(mode="rb")) as img:
                output_size = get_output_dimensions(max_size, img.width, img.height)
                output_img = self.create_thumbnail(img, output_size)

            image_file_model = self.add_image_file(
                thumbnail_name, output_img, output_size
            )

            setattr(self, size_name, image_file_model)

    def create_thumbnail(self, img, output_size):
        output_img = BytesIO()
        img.thumbnail(output_size)
        # Remove transparency values if they exist so that the image can be converted to JPEG.
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_img, format="JPEG", quality=90)
        return output_img


class Video(ThumbnailMixin, MediaBase):
    # from fvvideo

    class Meta:
        verbose_name = _("Video")
        verbose_name_plural = _("Videos")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.can_add_core_uncontrolled_data,
            "change": predicates.can_edit_core_uncontrolled_data,
            "delete": predicates.can_delete_core_uncontrolled_data,
        }

    # from fvm:content
    original = models.OneToOneField(
        VideoFile, related_name="video", null=True, on_delete=models.SET_NULL
    )

    # acknowledgement from fvm:recorder, fvm:source

    def __str__(self):
        return f"{self.title} / {self.site} (Video)"

    def generate_resized_images(self):
        """
        A function to generate a set of resized images when a Video model is saved
        """
        width = self.original.width
        height = self.original.height

        # Iterate over each of the output image sizes.
        for size_name, max_size in settings.IMAGE_SIZES.items():
            output_dimensions = get_output_dimensions(max_size, width, height)
            self.add_thumbnail(self.original.content, output_dimensions, size_name)

    def add_thumbnail(self, original_file, output_dimensions, size_name):
        with tempfile.TemporaryDirectory() as temp_dir:
            thumbnail_temp_path = self.get_thumbnail_temp_path(
                original_file, size_name, temp_dir
            )
            self.write_thumbnail_file(
                original_file, output_dimensions, thumbnail_temp_path
            )

            thumbnail_name = self.get_thumbnail_file_name(original_file, size_name)
            self.set_thumbnail_attribute(
                size_name, output_dimensions, thumbnail_temp_path, thumbnail_name
            )

    def get_thumbnail_file_name(self, original_file, size_name):
        input_name = original_file.name.split(".")[0]
        thumbnail_name = f"{input_name}_{size_name}.jpg"
        return thumbnail_name

    def get_thumbnail_temp_path(self, original_file, size_name, temp_dir):
        file_name = os.path.basename(original_file.name).split(".")[0]
        output_filename = f"{file_name}_{size_name}.jpg"
        temp_output_image_path = f"{temp_dir}/{output_filename}"
        return temp_output_image_path

    def write_thumbnail_file(self, original_file, output_dimensions, output_path):
        with get_local_video_file(original_file) as temp_file:
            try:
                (
                    ffmpeg.input(temp_file.name)
                    .filter("scale", output_dimensions[0], -1)
                    .output(output_path, vframes=1)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            except ffmpeg.Error as e:
                self.logger.error(
                    f"Failed to generate image for video file [{original_file.name}].\n"
                    f"Error: {e}\n"
                    f"{e.stderr.decode('utf8')}\n"
                )

    def set_thumbnail_attribute(
        self, attribute_name, dimensions, thumbnail_file_path, thumbnail_name
    ):
        with open(thumbnail_file_path, "rb") as output_image:
            image_file_model = self.add_image_file(
                thumbnail_name, output_image, dimensions
            )
            setattr(self, attribute_name, image_file_model)


class EmbeddedVideo(MediaBase):
    class Meta:
        verbose_name = _("Embedded Video")
        verbose_name_plural = _("Embedded Videos")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    content = EmbedVideoField()

    def __str__(self):
        return f"{self.title} / {self.site} (Embedded Video)"


class RelatedMediaMixin(models.Model):
    """
    Related media fields with standard names.
    """

    class Meta:
        abstract = True

    related_audio = models.ManyToManyField(Audio, blank=True)
    related_images = models.ManyToManyField(Image, blank=True)
    related_videos = models.ManyToManyField(Video, blank=True)
