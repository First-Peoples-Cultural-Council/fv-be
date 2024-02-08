from celery import shared_task

from backend.search.indexing.song_index import SongDocumentManager

# async pass-throughs to the document manager methods


@shared_task
def sync_song_in_index(instance_id):
    SongDocumentManager.sync_in_index(instance_id)


@shared_task
def remove_song_from_index(instance_id):
    SongDocumentManager.remove_from_index(instance_id)
