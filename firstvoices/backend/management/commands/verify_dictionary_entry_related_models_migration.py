import logging

from django.core.management.base import BaseCommand

from backend.models import (
    Acknowledgement,
    AlternateSpelling,
    DictionaryEntry,
    Note,
    Pronunciation,
    Translation,
)


class Command(BaseCommand):
    help = (
        "Verify that the migration #107 worked as expected. This command counts all entries that were previously "
        "stored in a many-to-one relationship, which are now converted to ArrayField(s)."
    )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        dictionary_entries = DictionaryEntry.objects.all()

        error_count = 0
        error_logs = []

        for dictionary_entry in dictionary_entries:
            notes_count = len(dictionary_entry.notes)
            translations_count = len(dictionary_entry.translations)
            acknowledgements_count = len(dictionary_entry.acknowledgements)
            alternate_spellings_count = len(dictionary_entry.alternate_spellings)
            pronunciations_count = len(dictionary_entry.pronunciations)

            model_count_map = {
                Note: notes_count,
                Translation: translations_count,
                Acknowledgement: acknowledgements_count,
                AlternateSpelling: alternate_spellings_count,
                Pronunciation: pronunciations_count,
            }

            # Verifying count for each related model
            for model, model_count in model_count_map.items():
                related_entries_count = model.objects.filter(
                    dictionary_entry=dictionary_entry
                ).count()
                if related_entries_count != model_count:
                    error_count += 1
                    error_logs.append(
                        f"{model} count mismatch for dictionary_entry with id: {str(dictionary_entry.id)}."
                    )

            if error_count > 0:
                logger.error("Error found. Please check the logs below")
                for log in error_logs:
                    logger.error(log)
            else:
                logger.info("Related models count verified without errors.")
