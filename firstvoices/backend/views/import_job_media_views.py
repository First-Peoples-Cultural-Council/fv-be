from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import mixins, parsers, viewsets
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from backend.models import ImportJob
from backend.models.media import SUPPORTED_FILETYPES, File, ImageFile, VideoFile
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.base_views import SiteContentViewSetMixin

from . import doc_strings


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
    http_method_names = ["get", "post"]
    queryset = ""

    parser_classes = [parsers.MultiPartParser]

    def get_validated_import_job(self):
        import_job_id = self.kwargs["importjob_pk"]
        import_jobs = ImportJob.objects.filter(id=import_job_id)

        if not import_jobs.exists():
            raise Http404

        import_job = import_jobs.first()

        # Check permissions on the site first
        perm = import_job.get_perm("view")
        if self.request.user.has_perm(perm, import_job):
            return import_job
        else:
            raise PermissionDenied

    def get_filetype(self, file):
        content_type = file.content_type
        if content_type in SUPPORTED_FILETYPES["image"]:
            filetype = ImageFile
        elif content_type in SUPPORTED_FILETYPES["video"]:
            filetype = VideoFile
        elif content_type in SUPPORTED_FILETYPES["audio"]:
            filetype = File
        else:
            raise ValidationError("Unsupported filetype.")

        return filetype

    def list(self, request, **kwargs):
        return Response([])

    def create(self, *args, **kwargs):
        user = self.request.user
        site = self.get_validated_site()
        import_job = self.get_validated_import_job()

        for file in self.request.FILES.getlist("file"):
            filetype = self.get_filetype(file)
            new_file = filetype(
                content=file,
                site=site,
                import_job=import_job,
                created_by=user,
                last_modified_by=user,
            )
            new_file.save()

        return Response(status=202)
