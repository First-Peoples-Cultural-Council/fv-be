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
        result = {
            "title": entry.title,
            "previous_custom_order": entry.custom_order,
            "new_custom_order": "",
        }
        logger.info(f"Recalculating sort order for {DictionaryEntry.title}")
        entry.save()
        result["new_custom_order"] = entry.custom_order
        results.append(result)

    return results
