from celery import shared_task

from backend.search.indexing.story_index import StoryDocumentManager

# async pass-throughs to the document manager methods


@shared_task
def sync_story_in_index(instance_id):
    StoryDocumentManager.sync_in_index(instance_id)


@shared_task
def remove_story_from_index(instance_id):
    StoryDocumentManager.remove_from_index(instance_id)
