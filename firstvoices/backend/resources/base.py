from import_export import fields, resources, widgets

from backend.models.constants import Visibility
from backend.models.media import Audio, Image, Video
from backend.models.sites import Site
from backend.resources.utils.import_export_widgets import (
    ArrayOfStringsWidget,
    AudienceBooleanFieldWidget,
    ChoicesWidget,
    UserForeignKeyWidget,
)


class BaseResource(resources.ModelResource):
    created_by = fields.Field(
        column_name="created_by",
        attribute="created_by",
        widget=UserForeignKeyWidget(),
    )
    last_modified_by = fields.Field(
        column_name="last_modified_by",
        attribute="last_modified_by",
        widget=UserForeignKeyWidget(),
    )

    class Meta:
        abstract = True


class SiteContentResource(BaseResource):
    site = fields.Field(
        column_name="site",
        attribute="site",
        widget=(widgets.ForeignKeyWidget(Site, "id")),
    )

    class Meta:
        abstract = True


class ControlledSiteContentResource(SiteContentResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    class Meta:
        abstract = True


class RelatedMediaResourceMixin(resources.ModelResource):
    related_audio = fields.Field(
        column_name="related_audio",
        attribute="related_audio",
        m2m_add=True,
        widget=widgets.ManyToManyWidget(Audio, separator=",", field="id"),
    )
    related_images = fields.Field(
        column_name="related_images",
        attribute="related_images",
        m2m_add=True,
        widget=widgets.ManyToManyWidget(Image, separator=",", field="id"),
    )
    related_videos = fields.Field(
        column_name="related_videos",
        attribute="related_videos",
        m2m_add=True,
        widget=widgets.ManyToManyWidget(Video, separator=",", field="id"),
    )
    related_video_links = fields.Field(
        column_name="related_video_links",
        attribute="related_video_links",
        widget=ArrayOfStringsWidget(),
    )

    class Meta:
        abstract = True


class AudienceMixin(resources.ModelResource):
    exclude_from_games = fields.Field(
        column_name="include_in_games",
        attribute="exclude_from_games",
        widget=AudienceBooleanFieldWidget(),
    )
    exclude_from_kids = fields.Field(
        column_name="include_on_kids_site",
        attribute="exclude_from_kids",
        widget=AudienceBooleanFieldWidget(),
    )

    class Meta:
        abstract = True
