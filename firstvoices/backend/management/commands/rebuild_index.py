from django.core.management.base import BaseCommand

from backend.management.commands._helper import rebuild_index
from backend.search.indices.dictionary_entry_document import (
    DictionaryEntryDocument,
    dictionary_entries,
)


class Command(BaseCommand):
    help = "Rebuild search index with the current objects present in the database."
    index_mappings = {
        "dictionary_entries": {
            "index": dictionary_entries,
            "document": DictionaryEntryDocument,
        }
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--index",
            dest="index_name",
            help="Name of the index to be rebuilt (optional)",
            default=None,
        )

    def handle(self, *args, **options):
        # If a index name is supplied, only rebuild that, else rebuild all
        index_name = options["index_name"]

        if index_name:
            index = self.index_mappings[index_name]["index"]
            index_document = self.index_mappings[index_name]["document"]
            rebuild_index(index, index_document)

        else:
            for mapping in self.index_mappings.values():
                index = mapping["index"]
                index_document = mapping["document"]
                rebuild_index(index, index_document)

        self.stdout.write(self.style.SUCCESS("Index rebuild complete."))
