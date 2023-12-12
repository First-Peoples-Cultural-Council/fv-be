import logging

from django.core.management.base import BaseCommand

from backend.management.commands._helper import get_valid_index_name, rebuild_index
from backend.search.documents.dictionary_entry_document import DictionaryEntryDocument
from backend.search.documents.media_document import MediaDocument
from backend.search.documents.song_document import SongDocument
from backend.search.documents.story_document import StoryDocument
from backend.search.indexing import LanguageIndexManager
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_LANGUAGE_INDEX,
    ELASTICSEARCH_MEDIA_INDEX,
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
        "media": {"index_name": ELASTICSEARCH_MEDIA_INDEX, "document": MediaDocument},
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--index",
            dest="index_name",
            help="Name of the index to be rebuilt (optional)",
            default=None,
        )

    def handle(self, *args, **options):
        # Setting logger level to get all logs
        logger = logging.getLogger("rebuild_index")
        logger.setLevel(logging.INFO)

        # special case for now, as a first step to refactoring
        if options["index_name"] == ELASTICSEARCH_LANGUAGE_INDEX:
            logger.info("Building language index")
            LanguageIndexManager.rebuild()

        # If an index name is supplied, only rebuild that, else rebuild all
        index_name = get_valid_index_name(self.index_mappings, options["index_name"])

        if index_name:
            index_document = self.index_mappings[index_name]["document"]
            rebuild_index(index_name, index_document)
        else:
            logger.info("Invalid or no index name provided. Building all indices.")
            for mapping in self.index_mappings.values():
                index_name = mapping["index_name"]
                index_document = mapping["document"]
                rebuild_index(index_name, index_document)

            # additional special case
            logger.info("Building language index")
            LanguageIndexManager.rebuild()

        logger.info("Index rebuild complete.")
