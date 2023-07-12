from django.db.models import TextChoices
from django.utils.translation import gettext as _

VALID_DOCUMENT_TYPES = ["word", "phrase"]

# Index names
ELASTICSEARCH_DICTIONARY_ENTRY_INDEX = "dictionary_entries"

# Error messages
ES_CONNECTION_ERROR = (
    "Elasticsearch server down. Document could not be updated in index. %s id: %s"
)
ES_NOT_FOUND_ERROR = (
    "Indexed document not found. Cannot update index for the specified operation."
    "operation: %s. %s id: %s"
)

# Page size
ES_PAGE_SIZE = 25

# Maximum page size
ES_MAX_RESULTS = 100


class SearchIndexEntryTypes(TextChoices):
    DICTIONARY_ENTRY = "dictionary_entry", _("dictionary_entry")
    # Songs and stories to be added later
