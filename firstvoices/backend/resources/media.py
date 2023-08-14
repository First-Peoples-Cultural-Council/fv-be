import uuid

from django.conf import settings
from django.db import connection
from scripts.utils.aws_download_utils import file_in_aws

from backend.models.media import (
    Audio,
    AudioSpeaker,
    Image,
    ImageFile,
    Person,
    Video,
    VideoFile,
)
from backend.resources.base import SiteContentResource


class PersonResource(SiteContentResource):
    class Meta:
        model = Person


class AudioResource(SiteContentResource):
    class Meta:
        model = Audio


class AudioSpeakerResource(SiteContentResource):
    class Meta:
        model = AudioSpeaker


class AudioSpeakerMigrationResource(AudioSpeakerResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        """Delete unused persons that are not used as AudioSpeakers."""
        if not dry_run:
            Person.objects.filter(site__in=dataset["site"]).exclude(
                id__in=dataset["speaker"]
            ).delete()


class VisialMediaResource(SiteContentResource):
    def __init__(self):
        super().__init__()
        self.file_instance_id = None

    def save_instance(
        self, instance, is_create, using_transactions=True, dry_run=False
    ):
        """
        Takes care of saving the object to the database.

        Objects can be created in bulk if ``use_bulk`` is enabled.

        :param instance: The instance of the object to be persisted.
        :param is_create: A boolean flag to indicate whether this is a new object
        to be created, or an existing object to be updated.
        :param using_transactions: A flag to indicate whether db transactions are used.
        :param dry_run: A flag to indicate dry-run mode.
        """
        self.before_save_instance(instance, using_transactions, dry_run)
        if self._meta.use_bulk:
            if is_create:
                self.create_instances.append(instance)
            else:
                self.update_instances.append(instance)
        else:
            if not using_transactions and dry_run:
                # we don't have transactions and we want to do a dry_run
                pass
            else:
                # Enable thumbnail generation if the file is in AWS else disable it
                if file_in_aws(
                    instance.original.content.name, settings.AWS_STORAGE_BUCKET_NAME
                ):
                    instance.save(generate_thumbnails=True)
                else:
                    instance.save(generate_thumbnails=False)
        self.after_save_instance(instance, using_transactions, dry_run)


class ImageResource(VisialMediaResource):
    class Meta:
        model = Image

    def before_import_row(self, row, **kwargs):
        file_id = uuid.uuid4()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO backend_imagefile (id, created, last_modified, height, width, content, site_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [
                    str(file_id),
                    row["created"],
                    row["last_modified"],
                    -1,
                    -1,
                    row["content"],
                    row["site"],
                ],
            )
        self.file_instance_id = file_id

    def before_save_instance(self, instance, using_transactions, dry_run):
        instance.original = ImageFile.objects.get(id=self.file_instance_id)


class VideoResource(VisialMediaResource):
    class Meta:
        model = Video

    def before_import_row(self, row, **kwargs):
        file_id = uuid.uuid4()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO backend_videofile (id, created, last_modified, height, width, content, site_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [
                    str(file_id),
                    row["created"],
                    row["last_modified"],
                    -1,
                    -1,
                    row["content"],
                    row["site"],
                ],
            )
        self.file_instance_id = file_id

    def before_save_instance(self, instance, using_transactions, dry_run):
        instance.original = VideoFile.objects.get(id=self.file_instance_id)
