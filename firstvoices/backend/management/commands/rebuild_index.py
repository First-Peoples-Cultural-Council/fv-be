import logging

from django.core.management.base import BaseCommand

from backend.management.commands._helper import rebuild_index
from backend.search.documents.dictionary_entry_document import DictionaryEntryDocument
from backend.search.documents.media_document import MediaDocument
from backend.search.indexing.language_index import LanguageIndexManager
from backend.search.indexing.song_index import SongIndexManager
from backend.search.indexing.story_index import StoryIndexManager
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
        "media": {"index_name": ELASTICSEARCH_MEDIA_INDEX, "document": MediaDocument},
    }
    index_managers = {
        ELASTICSEARCH_LANGUAGE_INDEX: LanguageIndexManager,
        ELASTICSEARCH_SONG_INDEX: SongIndexManager,
        ELASTICSEARCH_STORY_INDEX: StoryIndexManager,
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

        # If an index name is supplied, only rebuild that
        index_name = options["index_name"]

        if index_name:
            try:
                index_manager = self.index_managers[index_name]
                return index_manager.rebuild()
            except KeyError:
                logger.warning(
                    "Can't rebuild index for unrecognized alias: [%s]", index_name
                )
                return

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
                logger.info("Rebuilding %s", index_name)
                rebuild_index(index_name, index_document)
                logger.info("Finished rebuilding %s", index_name)

            # new index managers
            for manager in self.index_managers.values():
                manager.rebuild()

        logger.info("Index rebuild complete.")
