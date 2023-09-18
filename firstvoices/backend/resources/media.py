import logging
import uuid

from django.db import connection
from django.utils import timezone

from backend.models.media import Audio, AudioSpeaker, Image, Person, Video
from backend.resources.base import SiteContentResource

logger = logging.getLogger(__name__)


class PersonResource(SiteContentResource):
    class Meta:
        model = Person


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


class FileDirectInsertionResourceMixin:
    class Meta:
        abstract = True

    def before_import_row(self, row, **kwargs):
        file_id = uuid.uuid4()
        last_modified = row["last_modified"] if row["last_modified"] else timezone.now()
        created = row["created"] if row["created"] else timezone.now()
        try:
            self.insert_file_via_sql(
                str(file_id), created, last_modified, row["content"], row["site"]
            )
            row["original"] = str(file_id)
        except Exception as e:
            logging.error(f"Object {row['id']} could not be migrated: {e}")
            raise e
        return super().before_import_row(row, **kwargs)


class AudioResource(FileDirectInsertionResourceMixin, SiteContentResource):
    class Meta:
        model = Audio

    @staticmethod
    def insert_file_via_sql(file_id, created, last_modified, content, site):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO backend_file (id, created, last_modified, content, site_id) "
                "VALUES (%s, %s, %s, %s, %s)",
                [
                    file_id,
                    created,
                    last_modified,
                    content,
                    site,
                ],
            )


class VisualMediaResource(FileDirectInsertionResourceMixin, SiteContentResource):
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
                instance.save(generate_thumbnails=False)
        self.after_save_instance(instance, using_transactions, dry_run)


class ImageResource(VisualMediaResource):
    class Meta:
        model = Image

    @staticmethod
    def insert_file_via_sql(file_id, created, last_modified, content, site):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO backend_imagefile (id, created, last_modified, height, width, content, site_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [
                    str(file_id),
                    created,
                    last_modified,
                    -1,
                    -1,
                    content,
                    site,
                ],
            )


class VideoResource(VisualMediaResource):
    class Meta:
        model = Video

    @staticmethod
    def insert_file_via_sql(file_id, created, last_modified, content, site):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO backend_videofile (id, created, last_modified, height, width, content, site_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [
                    str(file_id),
                    created,
                    last_modified,
                    -1,
                    -1,
                    content,
                    site,
                ],
            )
