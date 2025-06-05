from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from elasticsearch.dsl import Search, connections
from elasticsearch.dsl.index import Index
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch.helpers import actions

from backend.search import es_logging
from firstvoices.settings import ELASTICSEARCH_DEFAULT_CONFIG


def search_by_id(document_id, index):
    s = Search(index=index).params(request_timeout=10)
    response = s.query("match", document_id=document_id).execute()
    hits = response["hits"]["hits"]
    return hits[0] if hits else None


class IndexManager:
    index = ""
    document_managers = []

    @classmethod
    def rebuild(cls):
        es_logging.logger.info(f"Building index: {cls.index}")

        es = connections.get_connection()
        current_index = cls._get_current_index(es)
        new_index = cls._create_new_write_index()

        try:
            cls._add_all(es)

        except Exception as e:
            # If we are not able to complete the new index, delete it and leave the current one as read + write alias
            es_logging.logger.error(
                "The following error occurred while adding documents to index [%s]. \
                Deleting new index, making current index default. "
                % cls.index
            )
            es_logging.logger.error(e)
            new_index.delete(ignore=404)
            raise e

        # Removing old index
        if current_index:
            current_index.delete(ignore=404)

        cls._remove_write_alias(es, new_index)
        es_logging.logger.info(f"Finished building index: {cls.index}")

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

        cls._add_document_types(new_index)

        alias = {cls.index: {"is_write_index": True}}
        new_index.aliases(**alias)

        new_index.create()

        return new_index

    @classmethod
    def _add_document_types(cls, index):
        documents = {manager.document for manager in cls.document_managers}

        for d in documents:
            index.document(d)

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
        for document_manager in cls.document_managers:
            document_manager.add_all(es)


class DocumentManager:
    index = ""
    document = None
    model = None

    @classmethod
    def refresh(cls):
        index = Index(cls.index)
        index.refresh()

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
            es_logging.log_connection_error(e, instance)
        except Exception as e:
            es_logging.log_fallback_exception(e, instance)

    @classmethod
    def update_in_index(cls, instance):
        try:
            cls._update_in_index(instance)
        except ConnectionError as e:
            es_logging.log_connection_error(e, instance)
        except NotFoundError:
            es_logging.log_not_found_info(instance)
        except Exception as e:
            es_logging.log_fallback_exception(e, instance)

    @classmethod
    def _update_in_index(cls, instance):
        existing_index_document = cls._find_in_index(instance.id)
        new_index_document = cls.create_index_document(instance)
        new_values = new_index_document.to_dict(False, False)
        existing_index_document.update(**new_values)
        cls.refresh()

    @classmethod
    def _find_in_index(cls, instance_id):
        search_result = search_by_id(instance_id, cls.index)
        if search_result:
            return cls.document.get(id=search_result["_id"])

        raise NotFoundError(
            "Document [%s] not found in index [%s]", instance_id, cls.index
        )

    @classmethod
    def remove_from_index(cls, instance_id):
        try:
            existing_index_document = cls._find_in_index(instance_id)
            existing_index_document.delete()
            cls.refresh()
        except ConnectionError as e:
            es_logging.log_connection_error_details(
                e, type(cls.model).__name__, instance_id
            )
        except NotFoundError:
            es_logging.log_not_found_info_details(type(cls.model).__name__, instance_id)
        except Exception as e:
            es_logging.log_fallback_exception_details(
                e, type(cls.model).__name__, instance_id
            )

    @classmethod
    def should_be_indexed(cls, instance):
        """Subclasses can override for custom indexing conditions, such as visibility."""
        return True

    @classmethod
    def sync_in_index(cls, instance_id):
        """
        Add, update, ignore, or remove indexing for the given instance, based on the conditions in should_be_indexed.
        When you know a model has been deleted, use remove_from_index for efficiency.

        NOTE that this will sync the index with the database state for the given ID, so you must
        commit your db transaction FIRST.
        """
        try:
            instance = cls.model.objects.get(pk=instance_id)
        except ObjectDoesNotExist:
            return cls.remove_from_index(instance_id)

        if cls.should_be_indexed(instance):
            try:
                cls._update_in_index(instance)
            except ConnectionError as e:
                es_logging.log_connection_error(e, instance)
            except NotFoundError:
                cls.add_to_index(instance)
            except Exception as e:
                es_logging.log_fallback_exception(e, instance)
        else:
            cls.remove_from_index(instance_id)

    @classmethod
    def add_all(cls, es):
        """
        Adds all documents to the index, via the provided ElasticSearch Connection.
        """
        # the bulk function is imported this way to allow mocking it in tests
        es_logging.logger.info(
            "Adding all indexable [%s] instances to [%s] index",
            cls.model.__name__,
            cls.index,
        )
        actions.bulk(es, cls._iterator())
        es_logging.logger.info(
            "Finished adding all indexable [%s] instances to [%s] index",
            cls.model.__name__,
            cls.index,
        )

    @classmethod
    def _get_all_instances(cls):
        return cls.model.objects.all()

    @classmethod
    def _iterator(cls):
        instances = cls._get_all_instances()

        for instance in instances:
            if cls.should_be_indexed(instance):
                index_document = cls.create_index_document(instance)
                yield index_document.to_dict(True)
