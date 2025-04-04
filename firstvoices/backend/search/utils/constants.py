from django.db.models import TextChoices
from django.utils.translation import gettext as _

from backend.models.constants import DEFAULT_TITLE_LENGTH

# retry_on_conflict for all update calls
RETRY_ON_CONFLICT = 10

# Only exact search will be used if the length of
# search term crosses this threshold
FUZZY_SEARCH_CUTOFF = 50

# Index names - /search endpoint
ELASTICSEARCH_DICTIONARY_ENTRY_INDEX = "dictionary_entries"
ELASTICSEARCH_SONG_INDEX = "songs"
ELASTICSEARCH_STORY_INDEX = "stories"
ELASTICSEARCH_MEDIA_INDEX = "media"

# Index name - /sites endpoint
ELASTICSEARCH_LANGUAGE_INDEX = "languages"

# Document types
TYPE_WORD = "word"
TYPE_PHRASE = "phrase"
TYPE_SONG = "song"
TYPE_STORY = "story"

# Media types
TYPE_AUDIO = "audio"
TYPE_DOCUMENT = "document"
TYPE_IMAGE = "image"
TYPE_VIDEO = "video"

ALL_SEARCH_TYPES = [
    TYPE_WORD,
    TYPE_PHRASE,
    TYPE_SONG,
    TYPE_STORY,
    TYPE_AUDIO,
    TYPE_DOCUMENT,
    TYPE_IMAGE,
    TYPE_VIDEO,
]

ENTRY_SEARCH_TYPES = [TYPE_WORD, TYPE_PHRASE, TYPE_SONG, TYPE_STORY]

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

UNKNOWN_CHARACTER_FLAG = "⚑"

LENGTH_FILTER_MAX = DEFAULT_TITLE_LENGTH


class SearchIndexEntryTypes(TextChoices):
    DICTIONARY_ENTRY = "dictionary_entry", _("dictionary_entry")
    SONG = "song", _("song")
    STORY = "story", _("story")
    MEDIA = "media", _("media")
