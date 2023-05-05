from celery import shared_task

from backend.models import Character


@shared_task
def some_expensive_operation(param: str):
    # for example:
    return Character.objects.filter(title__icontains=param).count()
