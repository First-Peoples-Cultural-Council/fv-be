from celery import shared_task
from django.apps import apps
from django.db import transaction


@shared_task
def generate_media_thumbnails(model_name: str, id: str):
    """
    Calls generate_resized_images on the specified media object
    """
    model_class = apps.get_model(app_label="backend", model_name=model_name)

    with transaction.atomic():
        # can raise DoesNotExist, but just let it flow up
        instance = model_class.objects.get(id=id)
        # again, let the exceptions be logged -- nothing useful we can do here
        instance.generate_resized_images()
