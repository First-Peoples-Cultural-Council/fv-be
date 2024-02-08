import pytest

from backend.search.indexing.song_index import SongDocumentManager
from backend.tests import factories


@pytest.fixture
def mock_index_methods(mocker):
    return {
        "mock_sync": mocker.patch.object(SongDocumentManager, "sync_in_index"),
        "mock_remove": mocker.patch.object(SongDocumentManager, "remove_from_index"),
    }


class TestSongIndexingSignals:
    @pytest.mark.django_db
    def test_new_song_is_synced(self, mock_index_methods):
        instance = factories.SongFactory.create()

        mock_index_methods["mock_sync"].assert_called_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_edited_song_is_synced(self, mock_index_methods):
        instance = factories.SongFactory.create()
        mock_index_methods["mock_sync"].reset_mock()

        instance.title = "New Title"
        instance.save()

        mock_index_methods["mock_sync"].assert_called_once_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_deleted_song_is_removed(self, mock_index_methods):
        instance = factories.SongFactory.create()
        instance_id = instance.id
        mock_index_methods["mock_sync"].reset_mock()

        instance.delete()

        mock_index_methods["mock_remove"].assert_called_once_with(instance_id)
        mock_index_methods["mock_sync"].assert_not_called()

    @pytest.mark.django_db
    def test_deleted_song_with_lyrics_is_removed(self, mock_index_methods):
        instance = factories.SongFactory.create()
        instance_id = instance.id
        factories.LyricsFactory.create(song=instance)
        mock_index_methods["mock_sync"].reset_mock()

        instance.delete()

        mock_index_methods["mock_remove"].assert_called_once_with(instance_id)

    @pytest.mark.django_db
    def test_new_lyric_related_song_is_synced(self, mock_index_methods):
        instance = factories.SongFactory.create()
        mock_index_methods["mock_sync"].reset_mock()
        factories.LyricsFactory.create(song=instance)

        mock_index_methods["mock_sync"].assert_called_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_edited_lyric_related_song_is_synced(self, mock_index_methods):
        instance = factories.SongFactory.create()
        lyric = factories.LyricsFactory.create(song=instance)
        mock_index_methods["mock_sync"].reset_mock()

        lyric.text = "New lyric text"
        lyric.save()

        mock_index_methods["mock_sync"].assert_called_once_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_deleted_lyric_related_song_is_synced(self, mock_index_methods):
        instance = factories.SongFactory.create()
        instance_id = instance.id
        lyric = factories.LyricsFactory.create(song=instance)
        mock_index_methods["mock_sync"].reset_mock()

        lyric.delete()

        mock_index_methods["mock_sync"].assert_called_once_with(instance_id)
        mock_index_methods["mock_remove"].assert_not_called()
