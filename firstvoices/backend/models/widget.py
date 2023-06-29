import rules
from django.db import models
from django.utils.translation import gettext as _

from backend.models.base import (
    BaseControlledSiteContentModel,
    BaseModel,
    BaseSiteContentModel,
)
from backend.permissions import predicates


class WidgetTypes(models.IntegerChoices):
    # enum intentionally has gaps to allow future changes to keep sequential order
    WIDGET_ALPHABET = 0
    WIDGET_APPS = 10
    WIDGET_CONTACT = 20
    WIDGET_GALLERY = 30
    WIDGET_IFRAME = 40
    WIDGET_KEYBOARDS = 50
    WIDGET_LOGO = 60
    WIDGET_LIST = 70
    WIDGET_QUOTES = 80
    WIDGET_STATS = 90
    WIDGET_TEXT = 100
    WIDGET_TEXTCONCISE = 110
    WIDGET_TEXTFULL = 120
    WIDGET_TEXTICONS = 130
    WIDGET_TEXTMULTI = 140
    WIDGET_WOTD = 150


class WidgetFormats(models.IntegerChoices):
    # enum intentionally has gaps to allow future changes to keep sequential order
    default = 0
    left = 10
    right = 20


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
    type = models.IntegerField(
        choices=WidgetTypes.choices, default=WidgetTypes.WIDGET_TEXT
    )
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
    title = models.CharField(max_length=225)

    def __str__(self):
        return f"{self.title} - [{self.site}]"


class SiteWidgetListOrder(BaseModel):
    class Meta:
        verbose_name = _("site widget list order")
        verbose_name_plural = _("site widget list orders")
        constraints = [
            models.UniqueConstraint(
                fields=["order", "site_widget_list"], name="unique_widget_order"
            ),
        ]
        rules_permissions = {
            "view": rules.always_allow,
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

    @property
    def site(self):
        return self.site_widget_list.site

    def __str__(self):
        return f"Widget [{self.site_widget}] - order [{self.order}] pair"
