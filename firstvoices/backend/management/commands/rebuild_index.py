import logging

from django.core.management.base import BaseCommand

from backend.search.indexing.dictionary_index import DictionaryIndexManager
from backend.search.indexing.language_index import LanguageIndexManager
from backend.search.indexing.media_index import MediaIndexManager
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
    index_managers = {
        ELASTICSEARCH_LANGUAGE_INDEX: LanguageIndexManager,
        ELASTICSEARCH_SONG_INDEX: SongIndexManager,
        ELASTICSEARCH_STORY_INDEX: StoryIndexManager,
        ELASTICSEARCH_MEDIA_INDEX: MediaIndexManager,
        ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: DictionaryIndexManager,
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--index",
            dest="index_name",
            help="Name of the index to be rebuilt (optional)",
            default=None,
        )
        parser.add_argument(
            "--site",
            dest="site_slug",
            help="Slug of the site to be re-indexed (optional)",
            default=None,
        )

    def handle(self, *args, **options):
        # Setting logger level to get all logs
        logger = logging.getLogger("rebuild_index")
        logger.setLevel(logging.INFO)

        index_name = options["index_name"]
        site_slug = options["site_slug"]

        if index_name:
            try:
                manager = self.index_managers[index_name]
                return manager.rebuild(site_slug=site_slug)
            except KeyError:
                logger.warning(
                    "Can't rebuild index for unrecognized alias: [%s]", index_name
                )
                return
        else:
            logger.info("No index name provided. Building all indices.")

            for manager in self.index_managers.values():
                manager.rebuild(site_slug=site_slug)

        logger.info("Index rebuild complete.")
