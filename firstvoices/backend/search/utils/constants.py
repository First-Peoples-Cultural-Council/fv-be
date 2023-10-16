from django.db.models import TextChoices
from django.utils.translation import gettext as _

VALID_DOCUMENT_TYPES = ["word", "phrase", "song", "story"]

# Index names
ELASTICSEARCH_DICTIONARY_ENTRY_INDEX = "dictionary_entries"
ELASTICSEARCH_SONG_INDEX = "songs"
ELASTICSEARCH_STORY_INDEX = "stories"
ELASTICSEARCH_MEDIA_INDEX = "media"

# Error messages
ES_CONNECTION_ERROR = (
    "Elasticsearch server down. %s Document could not be updated in index. %s id: %s"
)
ES_NOT_FOUND_ERROR = (
    "Indexed document not found. Cannot update index for the specified operation."
    "operation: %s. %s id: %s"
)

# Page size
ES_PAGE_SIZE = 25

# Maximum page size
ES_MAX_RESULTS = 100

# Retry policy
ES_RETRY_POLICY = {
    "max_retries": 3,
    "interval_start": 3,
    "interval_step": 1,
}


class SearchIndexEntryTypes(TextChoices):
    DICTIONARY_ENTRY = "dictionary_entry", _("dictionary_entry")
    SONG = "song", _("song")
    STORY = "story", _("story")
    MEDIA = "media", _("media")
