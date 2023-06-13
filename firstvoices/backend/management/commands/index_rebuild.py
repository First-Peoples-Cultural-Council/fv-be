from django.core.management.base import BaseCommand

from backend.management.commands._helper import delete_index
from backend.search.indices.dictionary_entry_document import (
    DictionaryEntryDocument,
    dictionary_entries,
)


class Command(BaseCommand):
    help = "Rebuild search index with the current objects present in the database."

    def handle(self, *args, **options):
        # Delete current index
        delete_status = delete_index(dictionary_entries)

        if delete_status["acknowledged"]:
            self.stdout.write("Index deletion successful.")

        # Initialize new index
        DictionaryEntryDocument.init()

        self.stdout.write(self.style.SUCCESS("Index rebuild complete."))
