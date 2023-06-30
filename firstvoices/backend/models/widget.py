import rules
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import (
    BaseControlledSiteContentModel,
    BaseModel,
    BaseSiteContentModel,
)
from backend.permissions import predicates


class WidgetFormats(models.IntegerChoices):
    default = 0
    left = 1
    right = 2


class Widget(BaseModel):
    class Meta:
        verbose_name = _("widget")
        verbose_name_plural = _("widgets")
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    title = models.CharField(max_length=225)
    widget_type = models.CharField(max_length=255, default="WIDGET_TEXT")
    format = models.IntegerField(
        choices=WidgetFormats.choices, default=WidgetFormats.default
    )

    def __str__(self):
        return self.title


class WidgetSettings(BaseModel):
    class Meta:
        verbose_name = _("widget setting")
        verbose_name_plural = _("widget settings")
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    widget = models.ForeignKey(
        Widget, on_delete=models.CASCADE, related_name="%(class)s_set"
    )
    key = models.CharField(max_length=225)
    value = models.TextField()

    def __str__(self):
        return self.key


class SiteWidget(Widget, BaseControlledSiteContentModel):
    class Meta:
        verbose_name = _("site widget")
        verbose_name_plural = _("site widgets")
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    def __str__(self):
        return self.title


class SiteWidgetList(BaseSiteContentModel):
    class Meta:
        verbose_name = _("site widget list")
        verbose_name_plural = _("site widget lists")
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    widgets = models.ManyToManyField(
        SiteWidget, related_name="sitewidget_set", through="SiteWidgetListOrder"
    )

    def save(self, *args, **kwargs):
        # If the site has changed then update the sites of the through model(s)
        existing_instance = SiteWidgetList.objects.filter(id=self.id).first()
        if existing_instance and self.site != existing_instance.site:
            for order in self.sitewidgetlistorder_set.all():
                order.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Widget list [{self.id}] for site [{self.site}]"


class SiteWidgetListOrder(BaseSiteContentModel):
    class Meta:
        verbose_name = _("site widget list order")
        verbose_name_plural = _("site widget list orders")
        constraints = [
            models.UniqueConstraint(
                fields=["order", "site_widget_list"], name="unique_widget_order"
            ),
        ]
        rules_permissions = {
            "view": predicates.has_visible_site,
            "add": predicates.is_superadmin,  # permissions will change when we add a write API
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }

    site_widget = models.ForeignKey(
        SiteWidget, on_delete=models.CASCADE, related_name="sitewidgetlistorder_set"
    )
    site_widget_list = models.ForeignKey(
        SiteWidgetList, on_delete=models.CASCADE, related_name="sitewidgetlistorder_set"
    )

    order = models.IntegerField()

    def save(self, *args, **kwargs):
        self.site = self.site_widget_list.site
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Widget [{self.site_widget}] - order [{self.order}] pair"
