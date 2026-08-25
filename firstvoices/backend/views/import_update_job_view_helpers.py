from django.urls import reverse
from redis.exceptions import ConnectionError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from backend.models.import_jobs import ImportJob, ImportJobStatus
from backend.tasks.send_email_tasks import send_email_task


def notify_job_ready(
    request,
    site_slug,
    job_id,
    detail_view_name,
    already_ready_message,
    requires_validation_message,
    subject,
    message_template,
    support_user_email,
):
    curr_job = ImportJob.objects.get(id=job_id)
    if curr_job.status == ImportJobStatus.READY_FOR_IMPORT:
        raise ValidationError(already_ready_message)

    if curr_job.validation_status != ImportJobStatus.COMPLETE:
        raise ValidationError(requires_validation_message)

    url = request.build_absolute_uri(
        reverse(
            detail_view_name,
            kwargs={"site_slug": site_slug, "pk": job_id},
        )
    )

    message = message_template.format(
        site_slug=site_slug,
        job_id=job_id,
        requester_email=request.user.email,
        url=url,
    )

    try:
        send_email_task.apply_async((subject, message, [support_user_email]))
        import_job = ImportJob.objects.get(id=job_id)
        import_job.status = ImportJobStatus.READY_FOR_IMPORT
        import_job.save()
    except ConnectionError as e:
        error_message = f"An error occurred: {e}. Please reach out to support to resolve this issue."
        raise ConnectionError(error_message)

    return Response(status=status.HTTP_202_ACCEPTED)
