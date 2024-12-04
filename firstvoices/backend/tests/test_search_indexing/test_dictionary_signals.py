import pytest

from backend.search.indexing.dictionary_index import DictionaryEntryDocumentManager
from backend.tests import factories
from backend.tests.test_search_indexing.base_indexing_tests import (
    BaseRelatedInstanceSignalTest,
    PauseIndexingSignalRelatedMixin,
)


class TestDictionaryEntryIndexingSignals(
    PauseIndexingSignalRelatedMixin, BaseRelatedInstanceSignalTest
):
    manager = DictionaryEntryDocumentManager
    factory = factories.DictionaryEntryFactory

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

    def assign_new_related_entry(self, instance):
        related_entry = factories.DictionaryEntryFactory.create()
        return factories.DictionaryEntryLinkFactory.create(
            from_dictionary_entry=instance, to_dictionary_entry=related_entry
        )

    def assign_new_related_entry_via_manager(self, instance):
        related_entry = factories.DictionaryEntryFactory.create()
        instance.related_dictionary_entries.add(related_entry)
        instance.save()
        return related_entry

    @pytest.mark.django_db
    def test_deleted_instance_with_category_is_removed(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()
            instance_id = instance.id
            self.assign_new_category(instance)

        mock_index_methods["mock_sync"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            instance.delete()

        mock_index_methods["mock_remove"].assert_called_once_with(instance_id)

    @pytest.mark.django_db
    def test_assign_category_main_instance_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            self.assign_new_category(instance)

        self.assert_only_update_called(instance, mock_index_methods)

    @pytest.mark.django_db
    def test_remove_category_main_instance_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()
            category_link = self.assign_new_category(instance)

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            category_link.delete()

        self.assert_only_update_called(instance, mock_index_methods)

    @pytest.mark.django_db
    def test_assign_category_m2m_main_instance_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            self.assign_new_category_via_manager(instance)

        mock_index_methods["mock_update"].assert_called_with(instance)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_remove_category_m2m_main_instance_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()
            category = self.assign_new_category_via_manager(instance)

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            instance.categories.remove(category)

        mock_index_methods["mock_update"].assert_called_with(instance)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_delete_category_m2m_main_instance_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()
            category = self.assign_new_category_via_manager(instance)

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            category.delete()

        self.assert_only_update_called(instance, mock_index_methods)

    @pytest.mark.django_db
    def test_assign_category_m2m_main_instance_paused(self, mock_index_methods):
        paused_site = factories.SiteFactory.create()
        factories.SiteFeatureFactory.create(
            site=paused_site, key="indexing_paused", is_enabled=True
        )
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=False):
            self.assign_new_category_via_manager(instance)

        mock_index_methods["mock_update"].assert_not_called()
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_remove_category_m2m_main_instance_paused(self, mock_index_methods):
        paused_site = factories.SiteFactory.create()
        factories.SiteFeatureFactory.create(
            site=paused_site, key="indexing_paused", is_enabled=True
        )
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()
            category = self.assign_new_category_via_manager(instance)

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=False):
            instance.categories.remove(category)

        mock_index_methods["mock_update"].assert_not_called()
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_delete_category_m2m_main_instance_paused(self, mock_index_methods):
        paused_site = factories.SiteFactory.create()
        factories.SiteFeatureFactory.create(
            site=paused_site, key="indexing_paused", is_enabled=True
        )
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()
            category = self.assign_new_category_via_manager(instance)

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=False):
            category.delete()

        mock_index_methods["mock_update"].assert_not_called()
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_assign_related_entry_instance_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            self.assign_new_related_entry(instance)

        mock_index_methods["mock_update"].assert_any_call(instance)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_assign_related_entry_m2m_main_instance_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            self.assign_new_related_entry_via_manager(instance)

        mock_index_methods["mock_update"].assert_called_with(instance)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_remove_related_entry_link_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = factories.DictionaryEntryFactory.create()
            related_entry = factories.DictionaryEntryFactory.create()
            dictionary_entry_link = factories.DictionaryEntryLinkFactory.create(
                from_dictionary_entry=instance, to_dictionary_entry=related_entry
            )

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            dictionary_entry_link.delete()

        mock_index_methods["mock_update"].assert_any_call(instance)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_remove_related_entry_m2m_main_instance_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()
            related_entry = self.assign_new_related_entry_via_manager(instance)

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            instance.related_dictionary_entries.remove(related_entry)

        mock_index_methods["mock_update"].assert_called_with(instance)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_remove_related_entry_instance_is_synced(self, mock_index_methods):
        with self.capture_on_commit_callbacks(execute=True):
            instance = self.factory.create()
            related_entry = self.assign_new_related_entry(instance)

        mock_index_methods["mock_sync"].reset_mock()
        mock_index_methods["mock_update"].reset_mock()

        with self.capture_on_commit_callbacks(execute=True):
            related_entry.delete()

        mock_index_methods["mock_update"].assert_any_call(instance)
