import factory
from factory.django import DjangoModelFactory

from backend.models.constants import Visibility
from backend.models.widget import (
    SiteWidget,
    SiteWidgetList,
    SiteWidgetListOrder,
    Widget,
    WidgetSettings,
)
from backend.tests.factories.base_factories import BaseSiteContentFactory


class WidgetFactory(DjangoModelFactory):
    class Meta:
        model = Widget

    title = factory.Sequence(lambda n: "Widget-%03d" % n)


class WidgetSettingsFactory(DjangoModelFactory):
    widget = factory.SubFactory(WidgetFactory)

    class Meta:
        model = WidgetSettings

    key = factory.Sequence(lambda n: "key: %03d" % n)
    value = factory.Sequence(lambda n: "value: %03d" % n)


class SiteWidgetFactory(BaseSiteContentFactory, WidgetFactory):
    class Meta:
        model = SiteWidget


class SiteWidgetListFactory(BaseSiteContentFactory):
    class Meta:
        model = SiteWidgetList


class SiteWidgetListOrderFactory(DjangoModelFactory):
    site_widget = factory.SubFactory(SiteWidgetFactory)
    site_widget_list = factory.SubFactory(SiteWidgetListFactory)

    class Meta:
        model = SiteWidgetListOrder

    order = factory.Sequence(int)


class SiteWidgetListWithTwoWidgetsFactory(SiteWidgetListFactory):
    widget_one = factory.RelatedFactory(
        SiteWidgetListOrderFactory,
        factory_related_name="site_widget_list",
        order=0,
        site_widget__visibility=Visibility.PUBLIC,
    )
    widget_two = factory.RelatedFactory(
        SiteWidgetListOrderFactory,
        factory_related_name="site_widget_list",
        order=1,
        site_widget__visibility=Visibility.PUBLIC,
    )


class SiteWidgetListWithEachWidgetVisibilityFactory(SiteWidgetListFactory):
    widget_public = factory.RelatedFactory(
        SiteWidgetListOrderFactory,
        factory_related_name="site_widget_list",
        site_widget__visibility=Visibility.PUBLIC,
    )
    widget_members = factory.RelatedFactory(
        SiteWidgetListOrderFactory,
        factory_related_name="site_widget_list",
        site_widget__visibility=Visibility.MEMBERS,
    )
    widget_team = factory.RelatedFactory(
        SiteWidgetListOrderFactory,
        factory_related_name="site_widget_list",
        site_widget__visibility=Visibility.TEAM,
    )


class SiteWidgetListWithThreeWidgetsFactory(SiteWidgetListFactory):
    widget_one = factory.RelatedFactory(
        SiteWidgetListOrderFactory,
        factory_related_name="site_widget_list",
        order=2,
        site_widget__visibility=Visibility.PUBLIC,
    )
    widget_two = factory.RelatedFactory(
        SiteWidgetListOrderFactory,
        factory_related_name="site_widget_list",
        order=0,
        site_widget__visibility=Visibility.PUBLIC,
    )
    widget_three = factory.RelatedFactory(
        SiteWidgetListOrderFactory,
        factory_related_name="site_widget_list",
        order=1,
        site_widget__visibility=Visibility.PUBLIC,
    )
