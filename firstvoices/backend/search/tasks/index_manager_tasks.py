from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction

from backend.search import es_logging, indexing
from backend.search.indexing import DocumentManager
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE, ASYNC_TASK_START_TEMPLATE
from firstvoices.celery import link_error_handler


def _get_manager(manager_name: str) -> DocumentManager:
    if not hasattr(indexing, manager_name):
        es_logging.logger.error(
            "Programming error. Class not found: [%s]", manager_name
        )
        return None

    return getattr(indexing, manager_name)


# async pass-throughs to the document manager methods


@shared_task
def sync_in_index(document_manager_name, instance_id):
    logger = get_task_logger(__name__)
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"document_manager_name: {document_manager_name}, instance_id: {instance_id}",
    )

    document_manager = _get_manager(document_manager_name)
    if document_manager:
        document_manager.sync_in_index(instance_id)

    logger.info(ASYNC_TASK_END_TEMPLATE)


@shared_task
def update_in_index(document_manager_name, instance_id):
    logger = get_task_logger(__name__)
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"document_manager_name: {document_manager_name}, instance_id: {instance_id}",
    )

    document_manager = _get_manager(document_manager_name)
    instance = document_manager.model.objects.filter(id=instance_id)
    if instance.exists() and document_manager:
        document_manager.update_in_index(instance.first())

    logger.info(ASYNC_TASK_END_TEMPLATE)


@shared_task
def remove_from_index(document_manager_name, instance_id):
    logger = get_task_logger(__name__)
    logger.info(
        ASYNC_TASK_START_TEMPLATE,
        f"document_manager_name: {document_manager_name}, instance_id: {instance_id}",
    )

    document_manager = _get_manager(document_manager_name)
    if document_manager:
        document_manager.remove_from_index(instance_id)

    logger.info(ASYNC_TASK_END_TEMPLATE)


# convenience methods for calling the async tasks


def request_index_task(task, document_manager, instance):
    instance_id = instance.id
    transaction.on_commit(
        lambda: task.apply_async(
            (
                document_manager.__name__,
                instance_id,
            ),
            link_error=link_error_handler.s(),
        )
    )


def request_sync_in_index(document_manager, instance):
    request_index_task(sync_in_index, document_manager, instance)


def request_update_in_index(document_manager, instance):
    request_index_task(update_in_index, document_manager, instance)


def request_remove_from_index(document_manager, instance):
    request_index_task(remove_from_index, document_manager, instance)
