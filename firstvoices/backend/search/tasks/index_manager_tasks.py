from celery import shared_task

from backend.search import es_logging, indexing
from firstvoices.celery import link_error_handler


def _get_document_manager(document_manager_name):
    if not hasattr(indexing, document_manager_name):
        es_logging.logger.error(
            "Programming error. Document manager not found: [%s]", document_manager_name
        )
        return None

    return getattr(indexing, document_manager_name)


# async pass-throughs to the document manager methods


@shared_task
def sync_in_index(document_manager_name, instance_id):
    document_manager = _get_document_manager(document_manager_name)
    if document_manager:
        document_manager.sync_in_index(instance_id)


@shared_task
def remove_from_index(document_manager_name, instance_id):
    document_manager = _get_document_manager(document_manager_name)
    if document_manager:
        document_manager.remove_from_index(instance_id)


# convenience methods for calling the async tasks


def request_sync_in_index(document_manager, instance):
    sync_in_index.apply_async(
        (
            document_manager.__name__,
            instance.id,
        ),
        link_error=link_error_handler.s(),
    )


def request_remove_from_index(document_manager, instance):
    remove_from_index.apply_async(
        (
            document_manager.__name__,
            instance.id,
        ),
        link_error=link_error_handler.s(),
    )
