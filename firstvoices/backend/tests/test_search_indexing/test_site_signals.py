import pytest

from backend.models.constants import Visibility
from backend.search.indexing import (
    AudioDocumentManager,
    DictionaryEntryDocumentManager,
    DictionaryIndexManager,
    ImageDocumentManager,
    MediaIndexManager,
    SongDocumentManager,
    SongIndexManager,
    StoryDocumentManager,
    StoryIndexManager,
    VideoDocumentManager,
)
from backend.tasks.constants import ASYNC_TASK_END_TEMPLATE
from backend.tests import factories
from backend.tests.utils import TransactionOnCommitMixin


class TestSiteSignals(TransactionOnCommitMixin):
    """Tests that site content is properly indexed on major Site changes."""

    index_managers = [
        DictionaryIndexManager,
        SongIndexManager,
        StoryIndexManager,
        MediaIndexManager,
    ]
    document_managers = [
        DictionaryEntryDocumentManager,
        SongDocumentManager,
        StoryDocumentManager,
        ImageDocumentManager,
        AudioDocumentManager,
        VideoDocumentManager,
    ]

    @pytest.fixture
    def index_manager_mocks(self, mocker):
        mocks = {}

        for manager in self.index_managers:
            prefix = manager.__name__ + "_"
            mocks[prefix + "rebuild"] = mocker.patch.object(manager, "rebuild")

        return mocks

    @pytest.fixture
    def document_manager_mocks(self, mocker):
        mocks = {}

        for manager in self.document_managers:
            prefix = manager.__name__ + "_"
            mocks[prefix + "remove_from_index"] = mocker.patch.object(
                manager, "remove_from_index"
            )

            mocks[prefix + "sync_in_index"] = mocker.patch.object(
                manager, "sync_in_index"
            )

        return mocks

    @pytest.mark.django_db
    def test_edit_site_title_does_not_affect_index(
        self, index_manager_mocks, document_manager_mocks, caplog
    ):
        with self.capture_on_commit_callbacks(execute=True):
            site = factories.SiteFactory.create()

        self.reset_all_mocks(index_manager_mocks)
        self.reset_all_mocks(document_manager_mocks)

        with self.capture_on_commit_callbacks(execute=True):
            site.title = "New title"
            site.save()

        self.assert_no_mocks_called(index_manager_mocks)
        self.assert_no_mocks_called(document_manager_mocks)

        # Verify that no task from site_indexing_tasks was started
        assert "site_content_indexing_tasks" not in caplog.text

    @pytest.mark.django_db
    def test_edit_site_visibility_syncs_index(
        self, index_manager_mocks, document_manager_mocks, caplog
    ):
        with self.capture_on_commit_callbacks(execute=True):
            site = factories.SiteFactory.create(visibility=Visibility.PUBLIC)
            dictionary_entry = factories.DictionaryEntryFactory.create(site=site)
            song = factories.SongFactory.create(site=site)
            story = factories.StoryFactory.create(site=site)
            audio = factories.AudioFactory.create(site=site)
            image = factories.ImageFactory.create(site=site)
            video = factories.VideoFactory.create(site=site)

        self.reset_all_mocks(index_manager_mocks)
        self.reset_all_mocks(document_manager_mocks)

        with self.capture_on_commit_callbacks(execute=True):
            site.visibility = Visibility.MEMBERS
            site.save()

        self.assert_document_synced(
            document_manager_mocks, DictionaryEntryDocumentManager, dictionary_entry
        )
        self.assert_document_synced(document_manager_mocks, SongDocumentManager, song)
        self.assert_document_synced(document_manager_mocks, StoryDocumentManager, story)
        self.assert_document_synced(document_manager_mocks, AudioDocumentManager, audio)
        self.assert_document_synced(document_manager_mocks, ImageDocumentManager, image)
        self.assert_document_synced(document_manager_mocks, VideoDocumentManager, video)

        assert f"Task started. Additional info: site: {site}" in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text

    @pytest.mark.django_db
    def test_delete_site_removes_all_content_from_index(
        self, index_manager_mocks, document_manager_mocks, caplog
    ):
        with self.capture_on_commit_callbacks(execute=True):
            site = factories.SiteFactory.create()
            dictionary_entry = factories.DictionaryEntryFactory.create(site=site)
            song = factories.SongFactory.create(site=site)
            story = factories.StoryFactory.create(site=site)
            audio = factories.AudioFactory.create(site=site)
            image = factories.ImageFactory.create(site=site)
            video = factories.VideoFactory.create(site=site)

        self.reset_all_mocks(index_manager_mocks)
        self.reset_all_mocks(document_manager_mocks)

        with self.capture_on_commit_callbacks(execute=True):
            site.delete()

        self.assert_document_removed(
            document_manager_mocks, DictionaryEntryDocumentManager, dictionary_entry
        )
        self.assert_document_removed(document_manager_mocks, SongDocumentManager, song)
        self.assert_document_removed(
            document_manager_mocks, StoryDocumentManager, story
        )
        self.assert_document_removed(
            document_manager_mocks, AudioDocumentManager, audio
        )
        self.assert_document_removed(
            document_manager_mocks, ImageDocumentManager, image
        )
        self.assert_document_removed(
            document_manager_mocks, VideoDocumentManager, video
        )

        assert f"Task started. Additional info: site: {site}" in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text

    @staticmethod
    def reset_all_mocks(mocks):
        for mock in mocks.values():
            mock.reset_mock()

    @staticmethod
    def assert_no_mocks_called(mocks):
        for mock in mocks.values():
            mock.assert_not_called()

    @staticmethod
    def assert_all_called_once_with(mocks, called_with):
        for mock in mocks.values():
            mock.assert_called_once_with(**called_with)

    @staticmethod
    def assert_document_removed(mocks, document_manager, instance):
        mocks[document_manager.__name__ + "_remove_from_index"].assert_called_once_with(
            instance.id
        )

    @staticmethod
    def assert_document_synced(mocks, document_manager, instance):
        mocks[document_manager.__name__ + "_sync_in_index"].assert_called_once_with(
            instance.id
        )
