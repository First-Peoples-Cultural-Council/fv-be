import uuid

from backend.search.tasks.index_manager_tasks import (
    remove_from_index,
    sync_in_index,
    update_in_index,
)
from backend.search.tasks.site_content_indexing_tasks import (
    remove_all_site_content_from_indexes,
    sync_all_media_site_content_in_indexes,
    sync_all_site_content_in_indexes,
)
from backend.tests.test_tasks.base_task_test import IgnoreTaskResultsMixin

# Tests for search task celery behaviour, not the actual search task functionality


class TestSyncInIndex(IgnoreTaskResultsMixin):
    TASK = sync_in_index

    def get_valid_task_args(self):
        return ["DocumentManager", uuid.uuid4()]


class TestUpdateInIndex(IgnoreTaskResultsMixin):
    TASK = update_in_index

    def get_valid_task_args(self):
        return ["DocumentManager", uuid.uuid4()]


class TestRemoveFromIndex(IgnoreTaskResultsMixin):
    TASK = remove_from_index

    def get_valid_task_args(self):
        return ["DocumentManager", uuid.uuid4()]


class TestRemoveAllSiteContentFromIndexes(IgnoreTaskResultsMixin):
    TASK = remove_all_site_content_from_indexes

    def get_valid_task_args(self):
        return [
            "site_title",
            {
                "dictionaryentry_set": [],
                "song_set": [],
                "story_set": [],
                "audio_set": [],
                "document_set": [],
                "image_set": [],
                "video_set": [],
            },
        ]


class TestSyncAllSiteContentInIndexes(IgnoreTaskResultsMixin):
    TASK = sync_all_site_content_in_indexes

    def get_valid_task_args(self):
        return [uuid.uuid4()]


class TestSyncAllMediaSiteContentInIndexes(IgnoreTaskResultsMixin):
    TASK = sync_all_media_site_content_in_indexes

    def get_valid_task_args(self):
        return [uuid.uuid4()]
