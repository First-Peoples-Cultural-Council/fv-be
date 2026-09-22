from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view

from backend.models.update_jobs import UpdateJob
from backend.views import doc_strings
from backend.views.api_doc_variables import id_parameter, site_slug_parameter
from backend.views.import_job_media_views import (
    ImportJobMediaViewSet as BatchJobMediaViewSet,
)


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
class UpdateJobMediaViewSet(BatchJobMediaViewSet):
    def get_validated_batch_job(self):
        batch_job_id = self.kwargs["updatejob_pk"]
        batch_jobs = UpdateJob.objects.filter(id=batch_job_id)

        if not batch_jobs.exists():
            raise Http404

        batch_job = batch_jobs.first()

        # Check permissions on the site first
        perm = batch_job.get_perm("view")
        if self.request.user.has_perm(perm, batch_job):
            return batch_job
        else:
            raise PermissionDenied
