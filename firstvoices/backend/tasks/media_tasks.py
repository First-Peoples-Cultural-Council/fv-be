from celery import shared_task
from celery.utils.log import get_task_logger
from django.apps import apps
from django.db import transaction

from backend.tasks.utils import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE


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
        # can raise DoesNotExist, but just let it flow up
        instance = model_class.objects.get(id=instance_id)
        # again, let the exceptions be logged -- nothing useful we can do here
        instance.generate_resized_images()
        instance.save(generate_thumbnails=False, set_modified_date=False)

    logger.info(ASYNC_TASK_END_TEMPLATE)
