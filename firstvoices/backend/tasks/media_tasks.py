from celery import shared_task
from celery.utils.log import get_task_logger
from django.apps import apps
from django.db import transaction

from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE


@shared_task
def generate_media_thumbnails(model_name: str, instance_id: str):
    """
    Calls generate_resized_images on the specified media object
    """
    logger = get_task_logger(__name__)
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"model_name: {model_name}, instance_id: {instance_id}",
    )

    model_class = apps.get_model(app_label="backend", model_name=model_name)

    with transaction.atomic():
        try:
            instance = model_class.objects.get(id=instance_id)
            instance.generate_resized_images()
            instance.save(generate_thumbnails=False, set_modified_date=False)
        except model_class.DoesNotExist:
            logger.warning(
                f"Thumbnail generation failed for {model_name} with id {instance_id}: Model not found."
            )
            logger.info(ASYNC_TASK_END_TEMPLATE)
            return

    logger.info(ASYNC_TASK_END_TEMPLATE)
