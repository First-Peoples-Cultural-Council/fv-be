from celery import shared_task

from backend.models import Alphabet, DictionaryEntry, Site


@shared_task
def recalculate_custom_order_preview(site_slug: str):
    """
    Generates a preview of the changes that will be made to the custom order
    and title of entries in a site's dictionary.
    """

    site = Site.objects.get(slug=site_slug)
    alphabet = Alphabet.objects.get(site=site)
    preview = {}

    # First, get the changes in custom order and title for every entry, and store entries with unknown characters
    updated_entries = []
    unknown_character_count = {}
    for entry in DictionaryEntry.objects.filter(site=site):
        original_title = entry.title
        original_custom_order = entry.custom_order

        cleaned_title = alphabet.clean_confusables(entry.title)
        new_order = alphabet.get_custom_order(cleaned_title)

        append_updated_entry(
            updated_entries,
            original_title,
            original_custom_order,
            cleaned_title,
            new_order,
        )

        # Count unknown characters remaining in each entry, first split by character, then apply custom order
        # If a "⚑" is in the custom order, it means that the character is unknown
        if "⚑" in new_order:
            chars = alphabet.get_character_list(cleaned_title)
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
    """
    Returns the same format as recalculate_custom_order_preview, but actually updates the custom order and
    title of entries in a site's dictionary by saving the entries.
    """

    site = Site.objects.get(slug=site_slug)
    alphabet = Alphabet.objects.get(site=site)
    results = {}

    updated_entries = []
    unknown_character_count = {}

    # Return the results of the recalculation i.e. the changes in custom order and title for every entry
    for entry in DictionaryEntry.objects.filter(site=site):
        original_title = entry.title
        original_custom_order = entry.custom_order

        # Save the entry to recalculate custom order and clean title
        entry.save()

        cleaned_title = entry.title
        new_order = entry.custom_order

        append_updated_entry(
            updated_entries,
            original_title,
            original_custom_order,
            cleaned_title,
            new_order,
        )

        # Count unknown characters remaining in each entry, first split by character, then apply custom order
        if "⚑" in new_order:
            chars = alphabet.get_character_list(entry.title)
            for char in chars:
                custom_order = alphabet.get_custom_order(char)
                if "⚑" in custom_order:
                    if custom_order not in unknown_character_count:
                        unknown_character_count[custom_order] = 0
                    unknown_character_count[custom_order] += 1

    results["unknown_character_count"] = unknown_character_count
    results["updated_entries"] = updated_entries

    return results


def append_updated_entry(
    updated_entries, original_title, original_custom_order, cleaned_title, new_order
):
    result = {
        "title": original_title,
        "cleaned_title": "",
        "is_title_updated": False,
        "previous_custom_order": original_custom_order,
        "new_custom_order": "",
    }

    if result["previous_custom_order"] != new_order:
        result["new_custom_order"] = new_order
    if result["title"] != cleaned_title:
        result["cleaned_title"] = cleaned_title
        result["is_title_updated"] = True

    if result["new_custom_order"] or result["cleaned_title"]:
        updated_entries.append(result)
