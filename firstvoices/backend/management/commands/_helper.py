from django.core.management import CommandError
from django.utils import timezone
from elasticsearch.helpers import bulk, errors
from elasticsearch_dsl import Index
from elasticsearch_dsl.connections import connections

from backend.models import DictionaryEntry, Song
from backend.search.indices import DictionaryEntryDocument, SongDocument
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_SONG_INDEX,
)
from backend.search.utils.object_utils import (
    get_acknowledgements_text,
    get_categories_ids,
    get_lyrics,
    get_notes_text,
    get_translation_text,
)
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG


def rebuild_index(index_name, index_document):
    es = connections.get_connection()

    # Get the latest index
    current_index = get_current_index(es, index_name)

    # Create new index with current timestamp
    current_timestamp = timezone.now().strftime("%Y_%m_%d_%H_%M_%S")
    new_index_name = index_name + "_" + current_timestamp
    new_index = Index(new_index_name)
    new_index.settings(
        number_of_shards=ELASTICSEARCH_DEFAULT_CONFIG["shards"],
        number_of_replicas=ELASTICSEARCH_DEFAULT_CONFIG["replicas"],
    )

    # Appointing the new index as the 'write' index while rebuilding
    new_index.document(index_document)
    new_index = add_write_alias(new_index, index_name)
    new_index.create()

    # Add all documents to the new index
    try:
        if index_name == ELASTICSEARCH_SONG_INDEX:
            bulk(es, song_iterator())
        elif index_name == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
            bulk(es, dictionary_entry_iterator())
    except errors.BulkIndexError as e:
        # Alias configuration error
        if "multiple indices" in str(e):
            raise CommandError(
                "There are multiple indices with same alias. Try clearing all indices and then "
                "rebuilding."
            )
    except Exception as e:
        # Any other exception due to which we are not able to build a new index or add documents to it
        # delete the new index so the current index is default index for both read and write
        new_index.delete(ignore=404)
        raise CommandError(
            "The following error occurred while indexing documents. Deleting new index, "
            + "making current index default. "
            + str(e)
        )

    # Removing old index
    if current_index:
        current_index.delete(ignore=404)

    # Removing and adding alias back to new index
    # This is done to remove the write rule added to this index
    # Only one index can be appointed as write index, for future rebuilding this rule needs to be removed
    # if we have only one index, it's write index by default
    new_index.delete_alias(using=es, name=index_name, ignore=404)
    new_index.put_alias(using=es, name=index_name)


def get_current_index(es_connection, index_name):
    all_indices = es_connection.indices.get_alias(index="*")
    related_indices = []
    for index in all_indices.keys():
        if str(index_name) in str(index):
            related_indices.append(index)

    if len(related_indices):
        related_indices = sorted(related_indices, reverse=True)
        return Index(related_indices[0])
    else:
        return None


def dictionary_entry_iterator():
    queryset = DictionaryEntry.objects.all()
    for entry in queryset:
        translations_text = get_translation_text(entry)
        notes_text = get_notes_text(entry)
        acknowledgements_text = get_acknowledgements_text(entry)
        categories = get_categories_ids(entry)

        index_entry = DictionaryEntryDocument(
            document_id=str(entry.id),
            site_id=str(entry.site.id),
            site_visibility=entry.site.visibility,
            title=entry.title,
            type=entry.type,
            translation=translations_text,
            acknowledgement=acknowledgements_text,
            note=notes_text,
            categories=categories,
            exclude_from_kids=entry.exclude_from_kids,
            exclude_from_games=entry.exclude_from_games,
            custom_order=entry.custom_order,
            visibility=entry.visibility,
        )
        yield index_entry.to_dict(True)


def song_iterator():
    queryset = Song.objects.all()
    for instance in queryset:
        lyrics_text, lyrics_translation_text = get_lyrics(instance)
        song_doc = SongDocument(
            document_id=str(instance.id),
            site_id=str(instance.site.id),
            site_visibility=instance.site.visibility,
            exclude_from_games=instance.exclude_from_games,
            exclude_from_kids=instance.exclude_from_kids,
            visibility=instance.visibility,
            title=instance.title,
            title_translation=instance.title_translation,
            note=instance.notes,
            acknowledgement=instance.acknowledgements,
            intro_title=instance.introduction,
            intro_translation=instance.introduction_translation,
            lyrics_text=lyrics_text,
            lyrics_translation=lyrics_translation_text,
        )
        yield song_doc.to_dict(True)


def add_write_alias(index, index_name):
    alias_config = {"is_write_index": True}

    if index_name == ELASTICSEARCH_DICTIONARY_ENTRY_INDEX:
        index.aliases(dictionary_entries=alias_config)
    elif index_name == ELASTICSEARCH_SONG_INDEX:
        index.aliases(songs=alias_config)
    return index


def get_valid_index_name(mappings, index_name):
    if index_name in mappings:
        return index_name
    else:
        return None
