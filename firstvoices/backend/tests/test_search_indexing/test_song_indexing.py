import pytest

from backend.models.constants import Visibility
from backend.search.indexing.song_index import SongDocumentManager, SongIndexManager
from backend.search.utils.constants import ELASTICSEARCH_SONG_INDEX
from backend.tests import factories
from backend.tests.test_search_indexing.base_tests import (
    BaseDocumentManagerTest,
    BaseIndexManagerTest,
)
from backend.tests.utils import assert_list


class TestSongIndexManager(BaseIndexManagerTest):
    manager = SongIndexManager
    factory = factories.SongFactory
    expected_index_name = ELASTICSEARCH_SONG_INDEX


class TestSongDocumentManager(BaseDocumentManagerTest):
    manager = SongDocumentManager
    factory = factories.SongFactory
    expected_index_name = ELASTICSEARCH_SONG_INDEX

    @pytest.mark.django_db
    def test_create_document(self):
        instance = self.factory.create(
            exclude_from_kids=False,
            exclude_from_games=True,
            visibility=Visibility.MEMBERS,
        )
        doc = self.manager.create_index_document(instance)

        assert doc.document_id == str(instance.id)
        assert doc.document_type == "Song"
        assert doc.site_id == str(instance.site.id)
        assert doc.site_visibility == instance.site.visibility

        assert doc.title == instance.title
        assert doc.title_translation == instance.title_translation
        assert doc.has_translation

        assert doc.note == instance.notes
        assert doc.acknowledgement == instance.acknowledgements
        assert doc.intro_title == instance.introduction
        assert doc.intro_translation == instance.introduction_translation

        assert_list(
            list(instance.lyrics.values_list("text", flat=True)), doc.lyrics_text
        )
        assert_list(
            list(instance.lyrics.values_list("translation", flat=True)),
            doc.lyrics_translation,
        )

        assert not doc.has_audio
        assert not doc.has_video
        assert not doc.has_image

        assert doc.exclude_from_games
        assert not doc.exclude_from_kids
        assert doc.visibility == Visibility.MEMBERS

        assert doc.created == instance.created
        assert doc.last_modified == instance.last_modified
