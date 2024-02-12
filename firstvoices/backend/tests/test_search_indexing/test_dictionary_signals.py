import pytest

from backend.search.indexing.dictionary_index import DictionaryEntryDocumentManager
from backend.tests import factories
from backend.tests.test_search_indexing.base_indexing_tests import (
    BaseRelatedInstanceSignalTest,
)


class TestDictionaryEntryIndexingSignals(BaseRelatedInstanceSignalTest):
    manager = DictionaryEntryDocumentManager
    factory = factories.DictionaryEntryFactory
    related_factories = [
        factories.NoteFactory,
        factories.AcknowledgementFactory,
        factories.TranslationFactory,
    ]

    def create_related_instance(self, related_factory, instance):
        return related_factory.create(dictionary_entry=instance)

    def assign_new_category(self, instance):
        category = factories.CategoryFactory.create()
        return factories.DictionaryEntryCategoryFactory.create(
            category=category, dictionary_entry=instance
        )

    def assign_new_category_via_manager(self, instance):
        category = factories.CategoryFactory.create()
        instance.categories.add(category)
        instance.save()
        return category

    @pytest.mark.django_db
    def test_deleted_instance_with_category_is_removed(self, mock_index_methods):
        instance = self.factory.create()
        instance_id = instance.id
        self.assign_new_category(instance)
        mock_index_methods["mock_sync"].reset_mock()

        instance.delete()

        mock_index_methods["mock_remove"].assert_called_once_with(instance_id)

    @pytest.mark.django_db
    def test_assign_category_main_instance_is_synced(self, mock_index_methods):
        instance = self.factory.create()
        mock_index_methods["mock_sync"].reset_mock()
        self.assign_new_category(instance)

        mock_index_methods["mock_sync"].assert_called_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_remove_category_main_instance_is_synced(self, mock_index_methods):
        instance = self.factory.create()
        category_link = self.assign_new_category(instance)
        mock_index_methods["mock_sync"].reset_mock()

        category_link.delete()

        mock_index_methods["mock_sync"].assert_called_once_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_assign_category_m2m_main_instance_is_synced(self, mock_index_methods):
        instance = self.factory.create()
        mock_index_methods["mock_sync"].reset_mock()
        self.assign_new_category_via_manager(instance)

        mock_index_methods["mock_sync"].assert_called_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_remove_category_m2m_main_instance_is_synced(self, mock_index_methods):
        instance = self.factory.create()
        category = self.assign_new_category_via_manager(instance)
        mock_index_methods["mock_sync"].reset_mock()

        instance.categories.remove(category)

        mock_index_methods["mock_sync"].assert_called_once_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_delete_category_m2m_main_instance_is_synced(self, mock_index_methods):
        instance = self.factory.create()
        category = self.assign_new_category_via_manager(instance)
        mock_index_methods["mock_sync"].reset_mock()

        category.delete()

        mock_index_methods["mock_sync"].assert_called_once_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()
