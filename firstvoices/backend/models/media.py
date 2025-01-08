import os.path
import sys
import tempfile
from io import BytesIO

import ffmpeg
import rules
from django.conf import settings
from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.models.fields import ArrayField
from embed_video.fields import EmbedVideoField
from PIL import Image as PILImage
from PIL import ImageOps

from backend.permissions import predicates
from backend.tasks.media_tasks import generate_media_thumbnails
from firstvoices.celery import link_error_handler

from .base import AudienceMixin, BaseModel, BaseSiteContentModel
from .constants import MAX_DESCRIPTION_LENGTH, MAX_FILEFIELD_LENGTH
from .files import File, FileBase, file_directory_path
from .validators import validate_no_duplicate_urls

SUPPORTED_FILETYPES = {
    # octet-stream is fallback for weird mp3 files; see fw-4829
    "audio": [
        "audio/wave",
        "audio/wav",
        "audio/x-wav",
        "audio/x-pn-wav",
        "audio/vnd.wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/mpeg3",
        "audio/x-mpeg-3",
        "application/octet-stream",
    ],
    "image": ["image/jpeg", "image/gif", "image/png", "image/tiff"],
    "video": ["video/mp4", "video/quicktime"],
}

# Alias so that migrations remain unedited
# see PR-1110 for more details
media_directory_path = file_directory_path


class Person(BaseSiteContentModel):
    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_at_least_editor_or_super,
            "change": predicates.is_at_least_editor_or_super,
            "delete": predicates.can_delete_media,
        }

    name = models.CharField(max_length=200)

    bio = models.CharField(max_length=1000, blank=True, null=False)

    def __str__(self):
        return f"{self.name} ({self.site})"


class VisualFileBase(FileBase):
    """A File model with additional height and width properties"""

    class Meta:
        abstract = True

    height = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)


class ImageFile(VisualFileBase):
    content = models.ImageField(
        upload_to=file_directory_path,
        max_length=MAX_FILEFIELD_LENGTH,
    )

    class Meta:
        verbose_name = _("Image File")
        verbose_name_plural = _("Image Files")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_at_least_assistant_or_super,
            "change": predicates.is_at_least_assistant_or_super,
            "delete": predicates.can_delete_media,
        }

    def get_image_dimensions(self):
        # separate function to get ability to mock it for tests
        return {
            "width": self.content.file.image.width,
            "height": self.content.file.image.height,
        }

    def save(self, update_file_metadata=False, **kwargs):
        try:
            image_dimensions = get_image_dimensions(self.content)
            self.width = image_dimensions[0]
            self.height = image_dimensions[1]

        except AttributeError as e:
            self.logger.info(
                f"Failed to get image dimensions for [{self.content.name}]. \n"
                f"Error: {e}\n"
            )

        super().save(update_file_metadata, **kwargs)


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
            "add": predicates.is_at_least_assistant_or_super,
            "change": predicates.is_at_least_assistant_or_super,
            "delete": predicates.can_delete_media,
        }

    def save(self, update_file_metadata=False, **kwargs):
        try:
            with get_local_video_file(self.content) as temp_file:
                video_info = self.get_video_info(temp_file)

            if video_info is None:
                self.logger.warning(
                    f"Failed to get video info for [{self.content.name}]. \n"
                )
            else:
                self.width = int(video_info["width"])
                self.height = int(video_info["height"])

        except ffmpeg.Error as e:
            self.logger.error(
                f"Failed to probe video file using ffmpeg [{self.content.name}]. \n"
                f"Error: {e}\n"
                f"{e.stderr.decode('utf8')}\n"
            )

        super().save(update_file_metadata, **kwargs)

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
    description = models.CharField(max_length=MAX_DESCRIPTION_LENGTH, blank=True)

    # see specific media models for migration info
    acknowledgement = models.TextField(max_length=500, blank=True)

    # exclude_from_games from fv-word:available_in_games, fvaudience:games

    # exclude_from_kids from fvaudience:children fvm:child_focused

    def save(self, generate_thumbnails=True, **kwargs):
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
            self.logger.warning(
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
            self.logger.warning(
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
            "add": predicates.is_at_least_assistant_or_super,
            "change": predicates.is_at_least_assistant_or_super,
            "delete": predicates.can_delete_media,
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
    if input_width <= max_size and input_height <= max_size:
        return input_width, input_height

    if input_width >= input_height:
        return (
            max_size,
            round(input_height / (input_width / max_size)),
        )

    return (
        round(input_width / (input_height / max_size)),
        max_size,
    )


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

    def save(self, generate_thumbnails=True, **kwargs):
        is_modifying_original = self._state.adding or self._is_updating_original()
        super().save(**kwargs)

        if generate_thumbnails and is_modifying_original:
            self._request_thumbnail_generation()

    def generate_resized_images(self):
        """
        A function to generate a set of resized images when the model is saved.
        """
        raise NotImplementedError

    def _request_thumbnail_generation(self):
        generate_media_thumbnails.apply_async(
            (self._meta.model_name, self.id), link_error=link_error_handler.s()
        )

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
            "add": predicates.is_at_least_assistant_or_super,
            "change": predicates.is_at_least_assistant_or_super,
            "delete": predicates.can_delete_media,
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
            try:
                original = self.original.content
            except AttributeError as e:
                self.logger.warning(
                    f"Thumbnail generation failed for image model {self.id}\n"
                    f"Error: Original image file not found: {e}\n"
                )
                return

            image_name = original.name.split(".")[0]
            thumbnail_name = f"{image_name}_{size_name}.jpg"
            try:
                with PILImage.open(original.file.open(mode="rb")) as img:
                    output_size = get_output_dimensions(max_size, img.width, img.height)

                    if img.mode in ("RGBA", "LA") or (
                        img.mode == "P" and "transparency" in img.info
                    ):
                        img = img.convert("RGBA")

                        # add a white background in case there are transparent areas
                        image_on_white = PILImage.new(
                            "RGBA", img.size, "WHITE"
                        )  # Create a white rgba background
                        image_on_white.paste(
                            img, (0, 0), img
                        )  # Paste the image on the background
                        image_on_white = image_on_white.convert("RGB")
                        output_img = self.create_thumbnail(image_on_white, output_size)
                    else:
                        output_img = self.create_thumbnail(img, output_size)

                    image_file_model = self.add_image_file(
                        thumbnail_name, output_img, output_size
                    )
                    setattr(self, size_name, image_file_model)
            except Exception as e:
                self.logger.warning(f"Error creating thumbnail for {image_name}")
                self.logger.warning(e)

    def create_thumbnail(self, img, output_size):
        output_img = BytesIO()
        img = ImageOps.exif_transpose(img)  # Handle orientation
        img.thumbnail(output_size)
        # Remove transparency values if they exist so that the image can be converted to JPEG.
        try:
            if img.mode != "RGB":
                img = img.convert("RGB")

            if (
                output_size[0] == img.width
                and output_size[1] == img.height
                and img.format == "JPEG"
            ):
                img.save(output_img, format="JPEG", quality="keep")
            else:
                img.save(output_img, format="JPEG", quality=80)
        except OSError as e:
            self.logger.warning(
                f"Failed to generate thumbnail for image file [{self.original.content.name}].\n"
                f"Error: {e}\n"
            )
        return output_img


class Video(ThumbnailMixin, MediaBase):
    # from fvvideo

    class Meta:
        verbose_name = _("Video")
        verbose_name_plural = _("Videos")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_at_least_assistant_or_super,
            "change": predicates.is_at_least_assistant_or_super,
            "delete": predicates.can_delete_media,
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
        if not self.original:
            self.logger.warning(
                f"Thumbnail generation failed for video model {self.id}\n"
                f"Error: Original video file not found.\n"
            )
            return

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


class RelatedMediaMixin(models.Model):
    """
    Related media fields with standard names.
    """

    class Meta:
        abstract = True

    related_audio = models.ManyToManyField(Audio, blank=True)
    related_images = models.ManyToManyField(Image, blank=True)
    related_videos = models.ManyToManyField(Video, blank=True)
    related_video_links = ArrayField(
        EmbedVideoField(),
        blank=True,
        default=list,
        validators=[validate_no_duplicate_urls],
    )
