import uuid

from django.db import transaction
from import_export import fields, resources, widgets
from import_export.results import RowResult

from backend.models.constants import Visibility
from backend.models.media import Audio, Image, Video
from backend.models.sites import Site
from backend.resources.utils.import_export_widgets import (
    ArrayOfStringsWidget,
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

    def __init__(self, site=None, run_as_user=None, import_job=None, **kwargs):
        super().__init__(**kwargs)
        self.site = site
        self.run_as_user = run_as_user
        self.import_job = import_job

    def before_import(self, dataset, **kwargs):
        # Adding required columns, since these will not be present in the headers
        dataset.append_col(lambda x: str(uuid.uuid4()), header="id")
        dataset.append_col(lambda x: str(self.site.id), header="site")
        dataset.append_col(lambda x: str(self.run_as_user), header="created_by")
        dataset.append_col(lambda x: str(self.run_as_user), header="last_modified_by")
        dataset.append_col(lambda x: str(self.import_job), header="import_job")

    def import_row(self, row, instance_loader, **kwargs):
        # Marking erroneous and invalid rows as skipped, then clearing the errors and validation_errors
        # so the valid rows can be imported

        try:
            with transaction.atomic():
                import_result = super().import_row(row, instance_loader, **kwargs)
                import_result.error_messages = []  # custom field to store messages
                import_result.number = kwargs["row_number"]

                if import_result.import_type in [
                    RowResult.IMPORT_TYPE_ERROR,
                    RowResult.IMPORT_TYPE_INVALID,
                ]:
                    raise ImportError("Row level error.")

        except ImportError:
            if import_result.import_type == RowResult.IMPORT_TYPE_INVALID:
                validation_error_messages = []
                for (
                    attribute,
                    error,
                ) in import_result.validation_error.message_dict.items():
                    validation_error_messages.append(f"{attribute}: {error[0]}")
                import_result.error_messages = validation_error_messages
                import_result.validation_error = None
            else:
                import_result.error_messages = [
                    str(err.error).split("\n")[0] for err in import_result.errors
                ]
                import_result.errors = []

            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result

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
        widget=ChoicesWidget(Visibility.choices, default=Visibility.TEAM),
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
