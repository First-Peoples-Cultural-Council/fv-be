import pytest

from backend.models.constants import Visibility
from backend.search.constants import ELASTICSEARCH_DICTIONARY_ENTRY_INDEX
from backend.search.indexing.dictionary_index import (
    DictionaryEntryDocumentManager,
    DictionaryIndexManager,
)
from backend.tests import factories
from backend.tests.factories import ImportJobFactory
from backend.tests.test_search_indexing.base_indexing_tests import (
    BaseDocumentManagerTest,
    BaseIndexManagerTest,
)
from backend.tests.utils import assert_list


class TestDictionaryIndexManager(BaseIndexManagerTest):
    manager = DictionaryIndexManager
    expected_index_name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX


class TestDictionaryEntryDocumentManager(BaseDocumentManagerTest):
    manager = DictionaryEntryDocumentManager
    factory = factories.DictionaryEntryFactory
    expected_index_name = ELASTICSEARCH_DICTIONARY_ENTRY_INDEX

    @pytest.mark.django_db
    def test_create_document(self):
        instance = self.factory.create(
            exclude_from_kids=False,
            exclude_from_games=True,
            visibility=Visibility.MEMBERS,
            translations=[],
        )
        doc = self.manager.create_index_document(instance)

        assert doc.document_id == str(instance.id)
        assert doc.document_type == "DictionaryEntry"
        assert doc.site_id == str(instance.site.id)
        assert doc.site_visibility == instance.site.visibility
        assert doc.visibility == Visibility.MEMBERS

        assert doc.title == instance.title
        assert not doc.has_translation
        assert doc.has_unrecognized_chars
        assert doc.custom_order == instance.custom_order
        assert doc.type == instance.type

        assert not doc.has_audio
        assert not doc.has_document
        assert not doc.has_image
        assert not doc.has_video
        assert not doc.has_categories
        assert not doc.has_related_entries

        assert doc.exclude_from_games
        assert not doc.exclude_from_kids

        assert doc.created == instance.created
        assert doc.last_modified == instance.last_modified

        assert not doc.import_job_id

    @pytest.mark.django_db
    def test_create_document_no_unknown_characters(self):
        site = factories.SiteFactory.create()
        factories.CharacterFactory.create(title="x", site=site)
        factories.CharacterFactory.create(title="y", site=site)
        factories.CharacterFactory.create(title="z", site=site)
        instance = self.factory.create(title="xyz", site=site)

        doc = self.manager.create_index_document(instance)

        assert not doc.has_unrecognized_chars

    @pytest.mark.django_db
    def test_create_document_related_models(self):
        import_job_instance = ImportJobFactory()
        instance = self.factory.create(import_job=import_job_instance)

        doc = self.manager.create_index_document(instance)

        assert_list(
            instance.translations,
            doc.translation,
        )
        assert_list(
            instance.acknowledgements,
            doc.acknowledgement,
        )
        assert_list(
            instance.notes,
            doc.note,
        )
        assert_list(
            list(instance.categories.values_list("id", flat=True)),
            doc.categories,
        )
        assert_list(instance.alternate_spellings, doc.alternate_spelling)

        assert doc.import_job_id == instance.import_job.id

    @pytest.mark.django_db
    def test_create_document_related_media(self):
        audio = factories.AudioFactory.create()
        document = factories.DocumentFactory.create()
        image = factories.ImageFactory.create()
        video = factories.VideoFactory.create()
        instance = self.factory.create(
            related_audio=[audio],
            related_documents=[document],
            related_images=[image],
            related_videos=[video],
        )

        doc = self.manager.create_index_document(instance)

        assert doc.has_audio
        assert doc.has_document
        assert doc.has_image
        assert doc.has_video

    @pytest.mark.django_db
    def test_create_document_related_entries(self):
        related_entry = factories.DictionaryEntryFactory.create()
        instance = self.factory.create()
        factories.DictionaryEntryLinkFactory(
            from_dictionary_entry=instance, to_dictionary_entry=related_entry
        )

        doc = self.manager.create_index_document(instance)

        assert doc.has_related_entries

    @pytest.mark.django_db
    def test_create_document_categories(self):
        instance = self.factory.create()
        category = factories.CategoryFactory.create()
        instance.categories.add(category)
        instance.save()

        doc = self.manager.create_index_document(instance)

        assert_list(
            [str(uuid) for uuid in instance.categories.values_list("id", flat=True)],
            doc.categories,
        )
        assert doc.has_categories

    @pytest.mark.django_db
    def test_create_document_with_speakers(self):
        site = factories.SiteFactory.create(visibility=Visibility.MEMBERS)
        instance = self.factory.create(
            exclude_from_kids=False, exclude_from_games=True, site=site
        )
        speaker1 = factories.PersonFactory.create(name="Speaker One", site=site)
        speaker2 = factories.PersonFactory.create(name="Speaker Two", site=site)
        speaker3 = factories.PersonFactory.create(name="Speaker Three", site=site)
        speaker4 = factories.PersonFactory.create(name="Speaker Four", site=site)

        audio1 = factories.AudioFactory.create(site=site)
        audio1.speakers.add(speaker1, speaker2)
        audio2 = factories.AudioFactory.create(site=site)
        audio2.speakers.add(speaker3, speaker4)

        instance.related_audio.add(audio1, audio2)

        doc = self.manager.create_index_document(instance)

        assert doc.speakers == [
            "Speaker One",
            "Speaker Two",
            "Speaker Three",
            "Speaker Four",
        ]
