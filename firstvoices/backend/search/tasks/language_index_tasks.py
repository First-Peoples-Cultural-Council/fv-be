from celery import shared_task

from backend.search.indexing.language_index import (
    LanguageDocumentManager,
    SiteDocumentManager,
)

# async pass-throughs to the document manager methods


@shared_task
def sync_language_in_index(language_id):
    LanguageDocumentManager.sync_in_index(language_id)


@shared_task
def remove_language_from_index(language_id):
    LanguageDocumentManager.remove_from_index(language_id)


@shared_task
def sync_site_in_language_index(site_id):
    SiteDocumentManager.sync_in_index(site_id)


@shared_task
def remove_site_from_language_index(site_id):
    SiteDocumentManager.remove_from_index(site_id)
