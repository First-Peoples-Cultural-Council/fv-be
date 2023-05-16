from celery import shared_task

from backend.models import Alphabet, DictionaryEntry, Site


@shared_task
def recalculate_custom_order_preview(site_slug: str):
    site = Site.objects.get(slug=site_slug)
    alphabet = Alphabet.objects.get(site=site)
    preview = {}

    # First count the number of occurrences of every unknown character
    unknown_character_count = {}
    for entry in DictionaryEntry.objects.filter(site=site, custom_order__contains="⚑"):
        chars = alphabet.get_character_list(entry.title)
        for char in chars:
            custom_order = alphabet.get_custom_order(char)
            if "⚑" in custom_order:
                if custom_order not in unknown_character_count:
                    unknown_character_count[custom_order] = 1
                unknown_character_count[custom_order] += 1

    # Then get the changes in custom order and title for every entry
    updated_entries = []
    for entry in DictionaryEntry.objects.filter(site=site):
        result = {
            "title": entry.title,
            "cleaned_title": "",
            "previous_custom_order": entry.custom_order,
            "new_custom_order": "",
        }

        cleaned_title = alphabet.clean_confusables(entry.title)
        new_order = alphabet.get_custom_order(entry.title)

        result["cleaned_title"] = cleaned_title
        result["new_custom_order"] = new_order

        if (
            result["previous_custom_order"] != result["new_custom_order"]
            or result["title"] != result["cleaned_title"]
        ):
            updated_entries.append(result)

    preview["unknown_character_count"] = unknown_character_count
    preview["updated_entries"] = updated_entries

    return preview
