import logging

from django.core.management.base import BaseCommand

from backend.management.commands._helper import rebuild_index
from backend.search.documents.dictionary_entry_document import DictionaryEntryDocument
from backend.search.documents.media_document import MediaDocument
from backend.search.documents.song_document import SongDocument
from backend.search.documents.story_document import StoryDocument
from backend.search.indexing.language_index import LanguageIndexManager
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
            return LanguageIndexManager.rebuild()

        # If an index name is supplied, only rebuild that
        index_name = options["index_name"]

        if index_name:
            try:
                index_document = self.index_mappings[index_name]["document"]
            except KeyError:
                logger.warning(
                    "Can't rebuild index for unrecognized alias: [%s]", index_name
                )
                return

            rebuild_index(index_name, index_document)
        else:
            logger.info("No index name provided. Building all indices.")
            for mapping in self.index_mappings.values():
                index_name = mapping["index_name"]
                index_document = mapping["document"]
                rebuild_index(index_name, index_document)

            # additional special case
            LanguageIndexManager.rebuild()

        logger.info("Index rebuild complete.")
