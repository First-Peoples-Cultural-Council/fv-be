import logging

from django.utils import timezone
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch.helpers import actions
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.index import Index

from backend.models.sites import Language
from backend.search.documents.language_document import LanguageDocument
from backend.search.logging import (
    log_connection_error,
    log_fallback_exception,
    log_not_found_error,
)
from backend.search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX
from backend.search.utils.get_index_documents import _fields_as_list, _text_as_list
from backend.search.utils.object_utils import search_by_id
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG, ELASTICSEARCH_LOGGER


class IndexManager:
    index = ""
    document = None
    models = None

    @classmethod
    def create_index_document(cls, instance):
        raise NotImplementedError()

    @classmethod
    def add_to_index(cls, instance):
        try:
            new_index_document = cls.create_index_document(instance)
            new_index_document.save()
            cls.refresh()
        except ConnectionError as e:
            log_connection_error(e, instance)
        except Exception as e:
            log_fallback_exception(e, instance)

    @classmethod
    def update_in_index(cls, instance):
        try:
            search_result = search_by_id(instance.id, cls.index)
            existing_index_document = cls.document.get(id=search_result["_id"])

            new_index_document = cls.create_index_document(instance)
            new_values = new_index_document.to_dict(False, False)

            existing_index_document.update(**new_values)

            cls.refresh()

        except ConnectionError as e:
            log_connection_error(e, instance)
        except NotFoundError as e:
            log_not_found_error(e, instance)
        except Exception as e:
            log_fallback_exception(e, instance)

    @classmethod
    def remove_from_index(cls, instance):
        try:
            search_result = search_by_id(instance.id, cls.index)
            existing_index_document = cls.document.get(id=search_result["_id"])
            existing_index_document.delete()
            cls.refresh()
        except ConnectionError as e:
            log_connection_error(e, instance)
        except NotFoundError as e:
            log_not_found_error(e, instance)
        except Exception as e:
            log_fallback_exception(e, instance)

    @classmethod
    def refresh(cls):
        index = Index(ELASTICSEARCH_LANGUAGE_INDEX)
        index.refresh()

    @classmethod
    def rebuild(cls):
        es = connections.get_connection()
        current_index = cls._get_current_index(es)
        new_index = cls._create_new_write_index()

        try:
            cls._add_all(es)

        except Exception as e:
            # If we are not able to complete the new index, delete it and leave the current one as read + write alias
            logger = logging.getLogger(ELASTICSEARCH_LOGGER)
            logger.error(
                "The following error occurred while adding documents to index [%s]. \
                Deleting new index, making current index default. "
                % cls.index
            )
            logger.error(e)
            new_index.delete(ignore=404)
            raise e

        # Removing old index
        if current_index:
            current_index.delete(ignore=404)

        cls._remove_write_alias(es, new_index)

    @classmethod
    def _get_current_index(cls, es_connection):
        all_indices = es_connection.indices.get_alias(index="*")
        related_indices = []
        for index, value in all_indices.items():
            if str(cls.index) in value["aliases"].keys():
                related_indices.append(index)

        if len(related_indices):
            related_indices = sorted(related_indices, reverse=True)
            return Index(related_indices[0])
        else:
            return None

    @classmethod
    def _create_new_write_index(cls):
        # Use new index as the 'write' index while rebuilding
        # This can lead to strange states if the rebuild fails -- see FW-5307
        current_timestamp = timezone.now().strftime("%Y_%m_%d_%H_%M_%S")
        new_index_name = cls.index + "_" + current_timestamp
        new_index = Index(new_index_name)

        new_index.settings(
            number_of_shards=ELASTICSEARCH_DEFAULT_CONFIG["shards"],
            number_of_replicas=ELASTICSEARCH_DEFAULT_CONFIG["replicas"],
        )

        new_index.document(cls.document)

        alias = {cls.index: {"is_write_index": True}}
        new_index.aliases(**alias)

        new_index.create()

        return new_index

    @classmethod
    def _remove_write_alias(cls, es, index):
        # Removing and adding alias back to new index
        # This is done to remove the write rule added to this index
        # Only one index can be appointed as write index, for future rebuilding this rule needs to be removed
        # if we have only one index, it's the write index by default
        index.delete_alias(using=es, name=cls.index, ignore=404)
        index.put_alias(using=es, name=cls.index)

    @classmethod
    def _add_all(cls, es):
        # the bulk function is imported this way to allow mocking it in tests
        actions.bulk(es, cls._iterator())

    @classmethod
    def _iterator(cls):
        for model in cls.models:
            instances = model.objects.all()
            for instance in instances:
                index_document = cls.create_index_document(instance)
                yield index_document.to_dict(True)


class LanguageIndexManager(IndexManager):
    index = ELASTICSEARCH_LANGUAGE_INDEX
    document = LanguageDocument
    models = [Language]

    @classmethod
    def create_index_document(cls, instance: Language):
        return cls.document(
            document_id=str(instance.id),
            document_type=instance.__class__.__name__,
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

    @classmethod
    def _iterator(cls):
        """
        Returns: iterator of all language models that have sites
        """
        for model in cls.models:
            instances = model.objects.all()
            for instance in instances:
                if instance.sites.all().exists():
                    index_document = cls.create_index_document(instance)
                    yield index_document.to_dict(True)
