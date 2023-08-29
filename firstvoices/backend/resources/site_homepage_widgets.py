from import_export import resources
from jwt_auth.models import User

from backend.models import Site
from backend.models.widget import SiteWidget, SiteWidgetList, SiteWidgetListOrder


class SiteHomepageWidgetsResource(resources.ModelResource):
    class Meta:
        model = Site
        fields = ("id",)

    @staticmethod
    def get_user_or_none(email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def before_import_row(self, row, row_number=None, **kwargs):
        if row["homepage_widgets"] != "":
            last_modified_by_user = self.get_user_or_none(row["last_modified_by"])
            created_by_user = self.get_user_or_none(row["created_by"])
            site = Site.objects.get(id=row["id"])
            widgets_list = row["homepage_widgets"].split(",")
            site_widget_list = SiteWidgetList.objects.create(
                site=site,
                last_modified_by=last_modified_by_user,
                last_modified=row["last_modified"],
                created_by=created_by_user,
                created=row["created"],
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
                    last_modified=row["last_modified"],
                    created_by=created_by_user,
                    created=row["created"],
                )
