from django.db import models
from django.utils.translation import gettext as _

from ..permissions import predicates
from .base import AudienceMixin, BaseSiteContentModel


class Person(BaseSiteContentModel):
    # from FVContributor

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    # from dc:title
    name = models.CharField(max_length=200)

    # from FVContributor dc:description
    bio = models.CharField(max_length=500)

    def __unicode__(self):
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
        Person, through="AudioSpeaker", null=True, related_name="audio_set"
    )

    def __unicode__(self):
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

    def __unicode__(self):
        return f"Audio Speaker {self.audio.title} - ({self.speaker.name})"


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

    def __unicode__(self):
        return f"{self.title} / {self.site} (Image)"


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

    def __unicode__(self):
        return f"{self.title} / {self.site} (Video)"
