import logging

from celery import shared_task

from backend.models import Character, DictionaryEntry, Site

logger = logging.getLogger(__name__)


@shared_task
def some_expensive_operation(param: str):
    # for example:
    return Character.objects.filter(title__icontains=param).count()


@shared_task
def recalculate_custom_sort_order(site_slug: str):
    site = Site.objects.get(slug=site_slug)
    results = []
    for entry in DictionaryEntry.objects.filter(site=site):
        logger.info(f"Recalculating sort order for {DictionaryEntry.title}")
        entry.save()
        results.append(entry.title)

    return results
