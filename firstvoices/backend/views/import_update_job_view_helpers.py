from django.urls import reverse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from redis.exceptions import ConnectionError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from backend.models.import_jobs import ImportJob, ImportJobStatus
from backend.tasks.send_email_tasks import send_email_task
from backend.views import doc_strings


def get_import_update_job_schema_view_config(
    *,
    serializer,
    site_slug_parameter,
    id_parameter,
    list_description,
    retrieve_description,
    create_description,
    destroy_description,
    confirm_description,
    validate_description,
    notify_description,
):
    detail_parameters = [site_slug_parameter, id_parameter]

    return {
        "list": extend_schema(
            description=list_description,
            responses={
                200: OpenApiResponse(
                    description=doc_strings.success_200_list,
                    response=serializer,
                ),
                403: OpenApiResponse(
                    description=doc_strings.error_403_site_access_denied
                ),
                404: OpenApiResponse(description=doc_strings.error_404_missing_site),
            },
            parameters=[site_slug_parameter],
        ),
        "retrieve": extend_schema(
            description=retrieve_description,
            responses={
                200: OpenApiResponse(
                    description=doc_strings.success_200_detail,
                    response=serializer,
                ),
                403: OpenApiResponse(description=doc_strings.error_403),
                404: OpenApiResponse(description=doc_strings.error_404),
            },
            parameters=detail_parameters,
        ),
        "create": extend_schema(
            description=create_description,
            responses={
                201: OpenApiResponse(
                    description=doc_strings.success_201,
                    response=serializer,
                ),
                400: OpenApiResponse(description=doc_strings.error_400_validation),
                403: OpenApiResponse(description=doc_strings.error_403),
                404: OpenApiResponse(description=doc_strings.error_404_missing_site),
            },
            parameters=[site_slug_parameter],
        ),
        "destroy": extend_schema(
            description=destroy_description,
            responses={
                204: OpenApiResponse(description=doc_strings.success_204_deleted),
                403: OpenApiResponse(description=doc_strings.error_403),
                404: OpenApiResponse(description=doc_strings.error_404_missing_site),
            },
            parameters=detail_parameters,
        ),
        "confirm": extend_schema(
            description=confirm_description,
            responses={
                202: OpenApiResponse(
                    description=doc_strings.success_202_job_accepted,
                    response=serializer,
                ),
                400: OpenApiResponse(description=doc_strings.error_400_validation),
                403: OpenApiResponse(description=doc_strings.error_403),
                404: OpenApiResponse(description=doc_strings.error_404_missing_site),
            },
            parameters=detail_parameters,
        ),
        "validate": extend_schema(
            description=validate_description,
            responses={
                202: OpenApiResponse(
                    description=doc_strings.success_202_job_accepted,
                ),
                400: OpenApiResponse(description=doc_strings.error_400_validation),
                403: OpenApiResponse(description=doc_strings.error_403),
                404: OpenApiResponse(description=doc_strings.error_404_missing_site),
            },
            parameters=detail_parameters,
        ),
        "notify": extend_schema(
            description=notify_description,
            responses={
                202: OpenApiResponse(
                    description=doc_strings.success_202_job_accepted,
                ),
                400: OpenApiResponse(description=doc_strings.error_400_validation),
                403: OpenApiResponse(description=doc_strings.error_403),
                404: OpenApiResponse(description=doc_strings.error_404_missing_site),
            },
            parameters=detail_parameters,
        ),
    }


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
