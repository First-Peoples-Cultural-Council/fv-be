from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, parsers, viewsets
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.status import HTTP_202_ACCEPTED

from backend.models import ImportJob
from backend.models.media import SUPPORTED_FILETYPES, File, ImageFile, VideoFile
from backend.models.update_jobs import UpdateJob
from backend.tasks.batch_utils import get_associated_filenames
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin


@extend_schema_view(
    create=extend_schema(
        description=_("Add media associated with an import-job."),
        responses={
            202: OpenApiResponse(
                description=doc_strings.success_202_import_job_media, response=""
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter, id_parameter],
    ),
    list=extend_schema(methods=["GET"], exclude=True),
)
class ImportJobMediaViewSet(
    SiteContentViewSetMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    http_method_names = ["post"]
    queryset = ""

    parser_classes = [parsers.MultiPartParser]

    @staticmethod
    def _get_job_relation_kwargs(job):
        if isinstance(job, ImportJob):
            return {"import_job": job}
        if isinstance(job, UpdateJob):
            return {"update_job": job}

        raise ValidationError(f"Unsupported job type for media upload: {type(job)}")

    def get_validated_batch_job(self):
        batch_job_id = self.kwargs["importjob_pk"]
        batch_jobs = ImportJob.objects.filter(id=batch_job_id)

        if not batch_jobs.exists():
            raise Http404

        batch_job = batch_jobs.first()

        # Check permissions on the site first
        perm = batch_job.get_perm("view")
        if self.request.user.has_perm(perm, batch_job):
            return batch_job
        else:
            raise PermissionDenied

    def get_filetype(self, file):
        content_type = file.content_type
        if content_type in SUPPORTED_FILETYPES["image"]:
            filetype = ImageFile
        elif content_type in SUPPORTED_FILETYPES["video"]:
            filetype = VideoFile
        elif (
            content_type in SUPPORTED_FILETYPES["audio"]
            or content_type in SUPPORTED_FILETYPES["document"]
        ):
            filetype = File
        else:
            raise ValidationError(f"Unsupported filetype. File: {file}")

        return filetype

    def create(self, *args, **kwargs):
        user = self.request.user
        site = self.get_validated_site()

        batch_job = self.get_validated_batch_job()
        if batch_job.status is not None:
            raise ValidationError(
                f"Can't add media after an import job has started. This job already has status: {batch_job.status}."
            )

        request_files = self.request.FILES.getlist("file")

        # Check filetypes raising an error if unsupported, and create a set of filenames in the request
        filenames = set()
        for file in request_files:
            self.get_filetype(file)
            filenames.add(file.name)

        #  Check for duplicate filenames within the request
        if len(request_files) > len(filenames):
            raise ValidationError(
                "There are one or more duplicate filenames within your upload."
            )

        #  Check for duplicate filenames compared with already uploaded files
        uploaded_filenames = get_associated_filenames(batch_job)

        if len(set(filenames).intersection(uploaded_filenames)) > 0:
            raise ValidationError(
                "You cannot upload a file with the same name as one already uploaded to this import job."
            )

        relation_kwargs = self._get_job_relation_kwargs(batch_job)
        for file in request_files:
            filetype = self.get_filetype(file)
            new_file = filetype(
                content=file,
                site=site,
                created_by=user,
                last_modified_by=user,
                **relation_kwargs,
            )
            new_file.save()

        return Response(status=HTTP_202_ACCEPTED)
