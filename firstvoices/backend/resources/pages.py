import logging

from import_export import fields
from jwt_auth.models import User

from backend.models import Image, Site, SitePage
from backend.models.constants import Visibility
from backend.models.media import Video
from backend.models.widget import SiteWidget, SiteWidgetList, SiteWidgetListOrder
from backend.resources.base import SiteContentResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class PageResource(SiteContentResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    class Meta:
        model = SitePage

    @staticmethod
    def get_user_or_none(email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def before_import_row(self, row, **kwargs):
        logger = logging.getLogger(__name__)

        # Create a SiteWidgetList object for each SitePage and convert the list of widget IDs to SiteWidgetListOrder
        # objects connecting the list to the widgets.
        if row["widgets"] == "":
            row["widgets"] = None
        else:
            last_modified_by_user = self.get_user_or_none(row["last_modified_by"])
            created_by_user = self.get_user_or_none(row["created_by"])
            site = Site.objects.get(id=row["site"])
            widgets_list = row["widgets"].split(",")
            site_widget_list = SiteWidgetList.objects.create(site=site)
            for index, widget_id in enumerate(widgets_list):
                widget = SiteWidget.objects.get(id=widget_id)
                SiteWidgetListOrder.objects.create(
                    site_widget=widget,
                    site_widget_list=site_widget_list,
                    order=index,
                    last_modified_by=last_modified_by_user,
                    created_by=created_by_user,
                )
            row["widgets"] = site_widget_list.id

        if row["banner_image"] and row["banner_image"] != "":
            try:
                Image.objects.get(id=row["banner_image"])
            except Image.DoesNotExist:
                logger.warning(
                    f"Image (banner) with ID ({row['banner_image']}) could not be found when creating SitePage with ID "
                    f"({row['id']})."
                )
                row["banner_image"] = None

        if row["banner_video"] and row["banner_video"] != "":
            try:
                Video.objects.get(id=row["banner_video"])
            except Image.DoesNotExist:
                logger.warning(
                    f"Video (banner) with ID ({row['banner_video']}) could not be found when creating SitePage with ID "
                    f"({row['id']})."
                )
                row["banner_video"] = None
