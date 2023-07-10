import rules
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import (
    BaseControlledSiteContentModel,
    BaseModel,
    BaseSiteContentModel,
)
from backend.models.constants import Visibility
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

    def save(self, **kwargs):
        if (
            not self._state.adding
            and self.visibility != SiteWidget.objects.get(pk=self.pk).visibility
        ):
            for order in self.sitewidgetlistorder_set.all():
                order.visibility = self.visibility
                order.save()
        super().save(**kwargs)


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
        SiteWidget, related_name="sitewidgetlist_set", through="SiteWidgetListOrder"
    )

    def __str__(self):
        return f"Widget list [{self.id}] for site [{self.site}]"

    def save(self, **kwargs):
        if (
            not self._state.adding
            and self.site != SiteWidgetList.objects.get(pk=self.pk).site
        ):
            for order in self.sitewidgetlistorder_set.all():
                order.save()
        super().save(**kwargs)


class SiteWidgetListOrder(BaseModel):
    class Meta:
        verbose_name = _("site widget list order")
        verbose_name_plural = _("site widget list orders")
        rules_permissions = {
            "view": predicates.is_visible_object,
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

    visibility = models.IntegerField(
        choices=Visibility.choices, null=True, blank=True, editable=False
    )
    site = models.ForeignKey(
        to="backend.Site",
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        null=True,
        blank=True,
        editable=False,
    )

    def save(self, **kwargs):
        self.visibility = self.site_widget.visibility
        self.site = self.site_widget_list.site
        super().save(**kwargs)

    def __str__(self):
        return f"Widget [{self.site_widget}] - order [{self.order}] pair"
