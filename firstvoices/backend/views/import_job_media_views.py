from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import mixins, parsers, viewsets
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from backend.models import ImportJob
from backend.models.media import SUPPORTED_FILETYPES, File, ImageFile, VideoFile
from backend.views.base_views import SiteContentViewSetMixin


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

        # Trigger update of validation-report for importJob

        return Response(status=202)
