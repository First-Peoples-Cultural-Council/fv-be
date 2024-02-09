from celery import shared_task

from backend.search import es_logging, indexing
from firstvoices.celery import link_error_handler


def _get_manager(manager_name):
    if not hasattr(indexing, manager_name):
        es_logging.logger.error(
            "Programming error. Class not found: [%s]", manager_name
        )
        return None

    return getattr(indexing, manager_name)


# async pass-throughs to the document manager methods


@shared_task
def sync_in_index(document_manager_name, instance_id):
    document_manager = _get_manager(document_manager_name)
    if document_manager:
        document_manager.sync_in_index(instance_id)


@shared_task
def remove_from_index(document_manager_name, instance_id):
    document_manager = _get_manager(document_manager_name)
    if document_manager:
        document_manager.remove_from_index(instance_id)


@shared_task
def rebuild_for_site(index_manager_name, site_slug):
    index_manager = _get_manager(index_manager_name)
    if index_manager:
        index_manager.rebuild(site_slug=site_slug)


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


def request_rebuild_for_site(index_manager, site):
    rebuild_for_site.apply_async(
        (
            index_manager.__name__,
            site.slug,
        ),
        link_error=link_error_handler.s(),
    )
