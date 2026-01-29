import pytest

from backend.models.constants import Visibility
from backend.search.constants import ELASTICSEARCH_MEDIA_INDEX
from backend.search.indexing import (
    AudioDocumentManager,
    DocumentDocumentManager,
    ImageDocumentManager,
    MediaIndexManager,
    VideoDocumentManager,
)
from backend.tests import factories
from backend.tests.test_search_indexing.base_indexing_tests import (
    BaseDocumentManagerTest,
    BaseIndexManagerTest,
)


class TestMediaIndexManager(BaseIndexManagerTest):
    manager = MediaIndexManager
    expected_index_name = ELASTICSEARCH_MEDIA_INDEX


class BaseMediaDocumentManagerTest(BaseDocumentManagerTest):
    expected_index_name = ELASTICSEARCH_MEDIA_INDEX
    expected_type = ""

    @pytest.mark.django_db
    def test_create_document(self):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        instance = self.factory.create(
            exclude_from_kids=False, exclude_from_games=True, site=site
        )
        doc = self.manager.create_index_document(instance)

        assert doc.document_id == str(instance.id)
        assert doc.document_type == self.expected_type
        assert doc.site_id == str(instance.site.id)
        assert doc.site_visibility == Visibility.MEMBERS
        assert doc.visibility == Visibility.PUBLIC

        assert doc.title == instance.title
        assert doc.filename == instance.original.content.name
        assert doc.description == instance.description
        assert doc.type == self.expected_type.lower()

        assert doc.exclude_from_games
        assert not doc.exclude_from_kids

        assert doc.created == instance.created
        assert doc.last_modified == instance.last_modified

    @pytest.mark.django_db
    def test_create_document_no_original(self):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        instance = self.factory.create(
            exclude_from_kids=False, exclude_from_games=True, site=site, original=None
        )
        doc = self.manager.create_index_document(instance)

        assert doc.document_id == str(instance.id)
        assert doc.document_type == self.expected_type
        assert doc.site_id == str(instance.site.id)
        assert doc.site_visibility == Visibility.MEMBERS
        assert doc.visibility == Visibility.PUBLIC

        assert doc.title == instance.title
        assert doc.filename is None
        assert doc.description == instance.description
        assert doc.type == self.expected_type.lower()

        assert doc.exclude_from_games
        assert not doc.exclude_from_kids

        assert doc.created == instance.created
        assert doc.last_modified == instance.last_modified


class TestAudioDocumentManager(BaseMediaDocumentManagerTest):
    manager = AudioDocumentManager
    factory = factories.AudioFactory
    expected_type = "Audio"

    @pytest.mark.django_db
    def test_create_document_with_speakers(self):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        instance = self.factory.create(
            exclude_from_kids=False, exclude_from_games=True, site=site
        )
        speaker1 = factories.PersonFactory.create(name="Speaker One", site=site)
        speaker2 = factories.PersonFactory.create(name="Speaker Two", site=site)
        instance.speakers.add(speaker1, speaker2)

        doc = self.manager.create_index_document(instance)

        assert doc.speakers == ["Speaker One", "Speaker Two"]


class TestDocumentDocumentManager(BaseMediaDocumentManagerTest):
    manager = DocumentDocumentManager
    factory = factories.DocumentFactory
    expected_type = "Document"


class TestImageDocumentManager(BaseMediaDocumentManagerTest):
    manager = ImageDocumentManager
    factory = factories.ImageFactory
    expected_type = "Image"


class TestVideoDocumentManager(BaseMediaDocumentManagerTest):
    manager = VideoDocumentManager
    factory = factories.VideoFactory
    expected_type = "Video"
