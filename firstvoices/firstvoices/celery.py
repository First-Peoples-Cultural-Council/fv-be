import logging
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "firstvoices.settings")

app = Celery("firstvoices")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

log = logging.getLogger("celery")


@app.task(ignore_result=True)
def link_error_handler(request, exc, traceback):
    log.error(f"Task {request.id} failed\n{exc}")
