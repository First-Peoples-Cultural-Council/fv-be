from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view

from backend.models import ImportJob
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.import_job_media_views import ImportJobMediaViewSet


@extend_schema_view(
    create=extend_schema(
        description=_("Add media associated with an update-job."),
        responses={
            202: OpenApiResponse(
                description=doc_strings.success_202_update_job_media, response=""
            ),
            400: OpenApiResponse(description=doc_strings.error_400_validation),
            403: OpenApiResponse(description=doc_strings.error_403),
            404: OpenApiResponse(description=doc_strings.error_404_missing_site),
        },
        parameters=[site_slug_parameter, id_parameter],
    ),
    list=extend_schema(methods=["GET"], exclude=True),
)
class UpdateJobMediaViewSet(ImportJobMediaViewSet):
    def get_validated_import_job(self):
        update_job_id = self.kwargs["updatejob_pk"]
        import_jobs = ImportJob.objects.filter(id=update_job_id)

        if not import_jobs.exists():
            raise Http404

        import_job = import_jobs.first()

        # Check permissions on the site first
        perm = import_job.get_perm("view")
        if self.request.user.has_perm(perm, import_job):
            return import_job
        else:
            raise PermissionDenied
