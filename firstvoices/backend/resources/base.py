import uuid

from django.db import transaction
from import_export import fields, resources, widgets
from import_export.results import RowResult

from backend.models import Document
from backend.models.constants import Visibility
from backend.models.import_jobs import ImportJob, ImportJobMode
from backend.models.media import Audio, Image, Video
from backend.models.sites import Site
from backend.models.update_jobs import UpdateJob
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

    system_last_modified_by = fields.Field(
        column_name="system_last_modified_by",
        attribute="system_last_modified_by",
        widget=UserForeignKeyWidget(),
    )

    def __init__(
        self,
        site=None,
        run_as_user=None,
        import_job=None,
        update_job=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.site = site
        self.run_as_user = run_as_user
        self.import_job = import_job
        self.update_job = update_job
        self.job = self.get_job_instance(import_job=import_job, update_job=update_job)
        self.created_by = self.job.created_by if self.job else ""

    @staticmethod
    def _get_job_id(job):
        return job.id if hasattr(job, "id") else job

    @classmethod
    def get_import_job_instance(cls, import_job):
        if isinstance(import_job, ImportJob):
            return import_job
        return ImportJob.objects.get(id=cls._get_job_id(import_job))

    @classmethod
    def get_update_job_instance(cls, update_job):
        if isinstance(update_job, UpdateJob):
            return update_job
        return UpdateJob.objects.get(id=cls._get_job_id(update_job))

    @classmethod
    def get_job_instance(cls, import_job=None, update_job=None):
        if update_job is not None:
            return cls.get_update_job_instance(update_job)

        if import_job is not None:
            return cls.get_import_job_instance(import_job)

        return None

    def before_import(self, dataset, **kwargs):
        # Adding required columns, since these will not be present in the headers
        # ID is only added if the import job mode is not update
        is_update_job = isinstance(self.job, UpdateJob)
        is_import_update_mode = (
            isinstance(self.job, ImportJob) and self.job.mode == ImportJobMode.UPDATE
        )

        if not is_update_job and not is_import_update_mode:
            dataset.append_col(lambda x: str(uuid.uuid4()), header="id")

        dataset.append_col(lambda x: str(self.site.id), header="site")
        dataset.append_col(lambda x: str(self.run_as_user), header="created_by")
        dataset.append_col(lambda x: str(self.run_as_user), header="last_modified_by")
        dataset.append_col(
            lambda x: str(self.created_by), header="system_last_modified_by"
        )
        if is_update_job:
            dataset.append_col(
                lambda x: str(self._get_job_id(self.update_job)), header="update_job"
            )
        else:
            dataset.append_col(
                lambda x: str(self._get_job_id(self.import_job)), header="import_job"
            )

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
                import_result = self._handle_validation_error(import_result)
            else:
                import_result.error_messages = [
                    str(err.error).split("\n")[0] for err in import_result.errors
                ]
                import_result.errors = []

            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result

    @staticmethod
    def _handle_validation_error(import_result):
        validation_error = import_result.validation_error
        validation_error_messages = []
        if hasattr(validation_error, "message_dict"):
            for (
                attribute,
                error,
            ) in import_result.validation_error.message_dict.items():
                validation_error_messages.append(f"{attribute}: {error[0]}")
        elif hasattr(validation_error, "error_list"):
            for err in import_result.validation_error.error_list:
                validation_error_messages.append(str(err).split("\n")[0])
        import_result.error_messages = validation_error_messages
        import_result.validation_error = None
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
    related_documents = fields.Field(
        column_name="related_documents",
        attribute="related_documents",
        m2m_add=True,
        widget=widgets.ManyToManyWidget(Document, separator=",", field="id"),
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
        column_name="video_embed_links",
        attribute="related_video_links",
        widget=ArrayOfStringsWidget(),
    )

    class Meta:
        abstract = True
