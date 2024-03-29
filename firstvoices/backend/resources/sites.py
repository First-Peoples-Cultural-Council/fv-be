from django.contrib.auth import get_user_model
from django.db import connection
from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models import SitePage
from backend.models.constants import Role, Visibility
from backend.models.media import File, ImageFile, VideoFile
from backend.models.sites import Language, Membership, Site
from backend.resources.base import BaseResource, SiteContentResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class SiteResource(BaseResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    language = fields.Field(
        column_name="language",
        attribute="language",
        widget=ForeignKeyWidget(Language, "title"),
    )

    class Meta:
        model = Site


class SiteMigrationResource(SiteResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        """Before importing sites that already exist, delete and import fresh."""
        if not dry_run:
            # Delete FileField objects from the database directly so that files are not removed from AWS when the
            # sites are deleted.
            imagefile_ids_to_delete = ImageFile.objects.filter(
                site__in=dataset["id"]
            ).values_list("id", flat=True)
            videofile_ids_to_delete = VideoFile.objects.filter(
                site__in=dataset["id"]
            ).values_list("id", flat=True)
            file_ids_to_delete = File.objects.filter(
                site__in=dataset["id"]
            ).values_list("id", flat=True)
            with connection.cursor() as cursor:
                if imagefile_ids_to_delete:
                    cursor.execute(
                        "DELETE FROM backend_imagefile WHERE id IN %s",
                        [tuple(imagefile_ids_to_delete)],
                    )
                if videofile_ids_to_delete:
                    cursor.execute(
                        "DELETE FROM backend_videofile WHERE id IN %s",
                        [tuple(videofile_ids_to_delete)],
                    )
                if file_ids_to_delete:
                    cursor.execute(
                        "DELETE FROM backend_file WHERE id IN %s",
                        [tuple(file_ids_to_delete)],
                    )

            # Delete SitePage objects since they cause the site deletion to fail due to on_delete protect (widgets).
            SitePage.objects.filter(site_id__in=dataset["id"]).delete()

            Site.objects.filter(id__in=dataset["id"]).delete()


class MembershipResource(SiteContentResource):
    role = fields.Field(
        column_name="role",
        widget=ChoicesWidget(Role.choices),
        attribute="role",
    )
    user = fields.Field(
        column_name="user",
        attribute="user",
        widget=ForeignKeyWidget(get_user_model(), field="email"),
    )

    class Meta:
        model = Membership

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Skip memberships that already exist."""
        membership_exists = Membership.objects.filter(
            user=instance.user, site=instance.site
        ).exists()
        if membership_exists:
            return True
        return super().skip_row(instance, original, row, import_validation_errors)
