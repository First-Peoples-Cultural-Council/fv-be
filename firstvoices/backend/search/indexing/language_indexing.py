from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch_dsl import Index

from backend.models.sites import Language
from backend.search.documents.language_document import LanguageDocument
from backend.search.indexing.logging import (
    log_connection_error,
    log_fallback_exception,
    log_not_found_error,
)
from backend.search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX
from backend.search.utils.get_index_documents import _fields_as_list, _text_as_list
from backend.search.utils.object_utils import search_by_id


def create_index_document(instance: Language):
    return LanguageDocument(
        language_name=instance.title,
        language_code=instance.language_code,
        language_alternate_names=_text_as_list(instance.alternate_names),
        language_community_keywords=_text_as_list(instance.community_keywords),
        site_names=_fields_as_list(instance.sites.all(), "title"),
        site_slugs=_fields_as_list(instance.sites.all(), "slug"),
        language_family_name=instance.language_family.title,
        language_family_alternate_names=_text_as_list(
            instance.language_family.alternate_names
        ),
    )


def add_to_index(language: Language):
    try:
        new_index_document = create_index_document(language)
        new_index_document.save()
        refresh()
    except ConnectionError as e:
        log_connection_error(e, language)
    except NotFoundError as e:
        log_not_found_error(e, language)
    except Exception as e:
        log_fallback_exception(e, language)


def update_in_index(language: Language):
    try:
        search_result = search_by_id(language.id, ELASTICSEARCH_LANGUAGE_INDEX)
        existing_index_document = LanguageDocument.get(id=search_result["_id"])

        new_index_document = create_index_document(language)
        new_values = new_index_document.to_dict(False, False)

        existing_index_document.update(**new_values)

        refresh()

    except ConnectionError as e:
        log_connection_error(e, language)
    except NotFoundError as e:
        log_not_found_error(e, language)
    except Exception as e:
        log_fallback_exception(e, language)


def remove_from_index(language: Language):
    try:
        search_result = search_by_id(language.id, ELASTICSEARCH_LANGUAGE_INDEX)
        existing_index_document = LanguageDocument.get(id=search_result["_id"])
        existing_index_document.delete()
        refresh()
    except ConnectionError as e:
        log_connection_error(e, language)
    except NotFoundError as e:
        log_not_found_error(e, language)
    except Exception as e:
        log_fallback_exception(e, language)


def refresh():
    index = Index(ELASTICSEARCH_LANGUAGE_INDEX)
    index.refresh()


def rebuild_language_index():
    pass
