from celery import shared_task

from backend.models import Alphabet, DictionaryEntry, Site


@shared_task
def recalculate_custom_order_preview(site_slug: str):
    site = Site.objects.get(slug=site_slug)
    alphabet = Alphabet.objects.get(site=site)
    preview = {}

    # First, get the changes in custom order and title for every entry, and store entries with unknown characters
    entries_with_unknown_chars = []
    updated_entries = []
    for entry in DictionaryEntry.objects.filter(site=site):
        result = {
            "title": entry.title,
            "cleaned_title": "",
            "previous_custom_order": entry.custom_order,
            "new_custom_order": "",
        }

        cleaned_title = alphabet.clean_confusables(entry.title)
        new_order = alphabet.get_custom_order(cleaned_title)

        result["cleaned_title"] = cleaned_title
        result["new_custom_order"] = new_order

        if "⚑" in new_order:
            entries_with_unknown_chars.append(entry)

        updated_entries.append(result)

    updated_entries = [
        entry
        for entry in updated_entries
        if entry["previous_custom_order"] != entry["new_custom_order"]
        or entry["cleaned_title"] != entry["title"]
    ]

    # Then get the count of unknown characters
    unknown_character_count = {}
    for entry in entries_with_unknown_chars:
        chars = alphabet.get_character_list(entry.title)
        for char in chars:
            custom_order = alphabet.get_custom_order(char)
            if "⚑" in custom_order:
                if custom_order not in unknown_character_count:
                    unknown_character_count[custom_order] = 0
                unknown_character_count[custom_order] += 1

    preview["unknown_character_count"] = unknown_character_count
    preview["updated_entries"] = updated_entries

    return preview


@shared_task
def recalculate_custom_order(site_slug: str):
    site = Site.objects.get(slug=site_slug)
    results = []

    # Return the results of the recalculation i.e. the changes in custom order and title for every entry
    for entry in DictionaryEntry.objects.filter(site=site):
        result = {
            "title": entry.title,
            "cleaned_title": "",
            "previous_custom_order": entry.custom_order,
            "new_custom_order": "",
        }
        entry.save()
        result["new_custom_order"] = entry.custom_order
        result["cleaned_title"] = entry.title
        if (
            result["previous_custom_order"] != result["new_custom_order"]
            or result["cleaned_title"] != result["title"]
        ):
            results.append(result)

    return results
