from import_export import resources

from backend.models import Site
from backend.models.widget import SiteWidget, SiteWidgetList, SiteWidgetListOrder
from backend.resources.utils.import_export_widgets import UserForeignKeyWidget


class SiteHomepageWidgetsResource(resources.ModelResource):
    class Meta:
        model = Site
        fields = ("id",)

    def before_import_row(self, row, row_number=None, **kwargs):
        if row["homepage_widgets"] != "":
            user_widget = UserForeignKeyWidget()
            last_modified_by_user = user_widget.clean(value=row["last_modified_by"])
            created_by_user = user_widget.clean(value=row["created_by"])

            site = Site.objects.get(id=row["id"])
            widgets_list = row["homepage_widgets"].split(",")
            site_widget_list = SiteWidgetList.objects.create(
                site=site,
                last_modified_by=last_modified_by_user,
                created_by=created_by_user,
            )
            site.homepage = site_widget_list
            site.save()
            for index, widget_id in enumerate(widgets_list):
                widget = SiteWidget.objects.get(id=widget_id)
                SiteWidgetListOrder.objects.create(
                    site_widget=widget,
                    site_widget_list=site_widget_list,
                    order=index,
                    last_modified_by=last_modified_by_user,
                    created_by=created_by_user,
                )
