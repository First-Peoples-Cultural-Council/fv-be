from django.core.management.base import BaseCommand

from backend.management.commands._helper import get_valid_index_name, rebuild_index
from backend.search.documents.dictionary_entry_document import DictionaryEntryDocument
from backend.search.documents.song_document import SongDocument
from backend.search.documents.story_document import StoryDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
)


class Command(BaseCommand):
    help = "Rebuild search index with the current objects present in the database."
    index_mappings = {
        "dictionary_entries": {
            "index_name": ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
            "document": DictionaryEntryDocument,
        },
        "songs": {
            "index_name": ELASTICSEARCH_SONG_INDEX,
            "document": SongDocument,
        },
        "stories": {"index_name": ELASTICSEARCH_STORY_INDEX, "document": StoryDocument},
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--index",
            dest="index_name",
            help="Name of the index to be rebuilt (optional)",
            default=None,
        )

    def handle(self, *args, **options):
        # If an index name is supplied, only rebuild that, else rebuild all
        index_name = get_valid_index_name(self.index_mappings, options["index_name"])

        if index_name:
            index_document = self.index_mappings[index_name]["document"]
            rebuild_index(index_name, index_document)
        else:
            self.stdout.write(
                "Invalid or no index name provided. Building all indices."
            )
            for mapping in self.index_mappings.values():
                index_name = mapping["index_name"]
                index_document = mapping["document"]
                rebuild_index(index_name, index_document)

        self.stdout.write(self.style.SUCCESS("Index rebuild complete."))
