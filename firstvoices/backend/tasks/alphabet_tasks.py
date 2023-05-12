from celery import shared_task

from backend.models import Alphabet, DictionaryEntry, Site


@shared_task
def recalculate_custom_order_preview(site_slug: str):
    site = Site.objects.get(slug=site_slug)
    alphabet = Alphabet.objects.get(site=site)
    preview = []
    for entry in DictionaryEntry.objects.filter(site=site):
        result = {
            "title": entry.title,
            "previous_custom_order": entry.custom_order,
            "new_custom_order": "",
        }
        new_order = alphabet.get_custom_order(entry.title)
        result["new_custom_order"] = new_order
        preview.append(result)

    return preview
