from celery import shared_task

from backend.models import Alphabet, DictionaryEntry, Site


@shared_task
def recalculate_custom_order_preview(site_slug: str):
    site = Site.objects.get(slug=site_slug)
    alphabet = Alphabet.objects.get(site=site)
    preview = {}

    # First, get the changes in custom order and title for every entry, and store entries with unknown characters
    updated_entries = []
    unknown_character_count = {}
    for entry in DictionaryEntry.objects.filter(site=site):
        result = {
            "title": entry.title,
            "is_title_updated": False,
            "cleaned_title": "",
            "previous_custom_order": entry.custom_order,
            "new_custom_order": "",
        }

        cleaned_title = alphabet.clean_confusables(entry.title)
        new_order = alphabet.get_custom_order(cleaned_title)

        if new_order != entry.custom_order:
            result["new_custom_order"] = new_order
        if cleaned_title != entry.title:
            result["cleaned_title"] = cleaned_title
            result["is_title_updated"] = True

        # Count unknown characters remaining in each entry, first split by character, then apply custom order
        # If a "⚑" is in the custom order, it means that the character is unknown
        if "⚑" in new_order:
            chars = alphabet.get_character_list(entry.title)
            for char in chars:
                custom_order = alphabet.get_custom_order(char)
                if "⚑" in custom_order:
                    if custom_order not in unknown_character_count:
                        unknown_character_count[custom_order] = 0
                    unknown_character_count[custom_order] += 1

        if result["new_custom_order"] or result["cleaned_title"]:
            updated_entries.append(result)

    preview["unknown_character_count"] = unknown_character_count
    preview["updated_entries"] = updated_entries

    return preview
