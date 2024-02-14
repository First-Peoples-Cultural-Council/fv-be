from unittest.mock import MagicMock, patch

import pytest
from elasticsearch import ConnectionError, NotFoundError

TEST_SEARCH_INDEX_ID = "test search index id"


class BaseIndexManagerTest:
    """
    Base test class for subclasses of IndexManager.

    To implement for testing your class, fill out managers, factory, and expected_index_name, and add tests for the
    create_index_document class.
    """

    manager = None
    expected_index_name = ""

    paths = {
        "es": "elasticsearch.Elasticsearch",
        "es_get_connection": "elasticsearch_dsl.connections.Connections.get_connection",
        "es_index_init": "elasticsearch_dsl.index.Index.__init__",
        "es_index_aliases": "elasticsearch_dsl.index.Index.aliases",
        "es_index_create": "elasticsearch_dsl.index.Index.create",
        "es_index_document": "elasticsearch_dsl.index.Index.document",
        "es_index_settings": "elasticsearch_dsl.index.Index.settings",
        "es_index_refresh": "elasticsearch_dsl.index.Index.refresh",
        "es_bulk": "elasticsearch.helpers.actions.bulk",
        "es_search_init": "elasticsearch_dsl.search.Search.__init__",
        "es_search_params": "elasticsearch_dsl.search.Search.params",
        "log_error": "logging.Logger.error",
        "log_warning": "logging.Logger.warning",
        "log_info": "logging.Logger.info",
    }

    def setup_method(self):
        manager_full_module = self.manager.__module__ + "." + self.manager.__name__

        # paths for internal manager methods
        self.paths["create_index_document"] = (
            manager_full_module + ".create_index_document"
        )
        self.paths["_get_current_index"] = manager_full_module + "._get_current_index"
        self.paths["_create_new_write_index"] = (
            manager_full_module + "._create_new_write_index"
        )

    def test_get_current_index_success(self):
        mock_es_connection = MagicMock()
        mock_es_connection.indices.get_alias.return_value = {
            "index_3": {"aliases": {self.expected_index_name: {}}},
            "index_1": {"aliases": {self.expected_index_name: {}}},
            "index_5": {"aliases": {self.expected_index_name: {}}},
            "index_2": {"aliases": {"a_different_index": {}}},
            "index_4": {"aliases": {"something_else": {}}},
        }

        with patch(self.paths["es_index_init"], return_value=None) as mock_index_init:
            index = self.manager._get_current_index(mock_es_connection)

            mock_index_init.assert_called_once_with("index_5")
            assert index is not None

    def test_get_current_index_none(self):
        mock_es_connection = MagicMock()
        mock_es_connection.indices.get_alias.return_value = {
            "index_2": {"aliases": {"a_different_index": {}}},
            "index_4": {"aliases": {"something_else": {}}},
        }

        with patch(self.paths["es_index_init"], return_value=None) as mock_index_init:
            index = self.manager._get_current_index(mock_es_connection)

            mock_index_init.assert_not_called()
            assert index is None

    def test_create_new_write_index(self):
        with patch(self.paths["es_index_init"], return_value=None) as mock_init, patch(
            self.paths["es_index_aliases"]
        ) as mock_aliases, patch(self.paths["es_index_create"]) as mock_create, patch(
            self.paths["es_index_document"]
        ), patch(
            self.paths["es_index_settings"]
        ) as mock_settings:
            self.manager._create_new_write_index()
            mock_init.assert_called_once()
            mock_aliases.assert_called_once_with(
                **{self.expected_index_name: {"is_write_index": True}}
            )
            mock_settings.assert_called_once_with(
                number_of_shards=1, number_of_replicas=0
            )
            mock_create.assert_called_once()

    def test_rebuild_success_no_current_index(self):
        mock_connection = MagicMock()
        mock_new_index = MagicMock()

        with patch(
            self.paths["es_get_connection"], return_value=mock_connection
        ), patch(self.paths["_get_current_index"], return_value=None), patch(
            self.paths["_create_new_write_index"], return_value=mock_new_index
        ) as mock_create_new_write_index, patch(
            self.paths["es_bulk"]
        ) as mock_bulk:
            self.manager.rebuild()
            mock_create_new_write_index.assert_called_once()

            # adds docs
            assert len(self.manager.document_managers) == mock_bulk.call_count

            # removes write alias from new index, to prepare for next rebuild
            mock_new_index.delete_alias.assert_called_once_with(
                using=mock_connection, name=self.expected_index_name, ignore=404
            )
            mock_new_index.put_alias.assert_called_once_with(
                using=mock_connection, name=self.expected_index_name
            )

    @pytest.mark.django_db
    def test_rebuild_failure_es_error(self):
        with patch(
            self.paths["es_get_connection"], side_effect=ConnectionError("Broken!")
        ):
            with pytest.raises(ConnectionError):
                self.manager.rebuild()

    @pytest.mark.django_db
    def test_rebuild_failure_adding_document(self):
        mock_connection = MagicMock()
        mock_new_index = MagicMock()

        with patch(
            self.paths["es_get_connection"], return_value=mock_connection
        ), patch(self.paths["_get_current_index"], return_value=None), patch(
            self.paths["_create_new_write_index"], return_value=mock_new_index
        ), patch(
            self.paths["es_bulk"], side_effect=Exception("Boom!")
        ):
            with pytest.raises(Exception):
                self.manager.rebuild()

                mock_new_index.delete.assert_called_once()

    def create_search_mocks(self):
        mock_query = MagicMock()
        mock_query.execute.return_value = {
            "hits": {"hits": [{"_id": TEST_SEARCH_INDEX_ID}]}
        }
        mock_search_obj = MagicMock()
        mock_search_obj.query.return_value = mock_query
        return mock_query, mock_search_obj

    def get_mock_document_with_es_error(self):
        mock_document = MagicMock()
        mock_document.save.side_effect = ConnectionError("Uh oh!")
        return mock_document


class BaseDocumentManagerTest:
    """
    Base test class for subclasses of DocumentManager.

    To implement for testing your class, fill out manager, factory, and expected_index_name, and add tests for the
    create_index_document class.
    """

    manager = None
    factory = None
    expected_index_name = ""

    paths = {
        "es": "elasticsearch.Elasticsearch",
        "es_get_connection": "elasticsearch_dsl.connections.Connections.get_connection",
        "es_index_init": "elasticsearch_dsl.index.Index.__init__",
        "es_index_aliases": "elasticsearch_dsl.index.Index.aliases",
        "es_index_create": "elasticsearch_dsl.index.Index.create",
        "es_index_document": "elasticsearch_dsl.index.Index.document",
        "es_index_settings": "elasticsearch_dsl.index.Index.settings",
        "es_index_refresh": "elasticsearch_dsl.index.Index.refresh",
        "es_bulk": "elasticsearch.helpers.actions.bulk",
        "es_search_init": "elasticsearch_dsl.search.Search.__init__",
        "es_search_params": "elasticsearch_dsl.search.Search.params",
        "log_error": "logging.Logger.error",
        "log_warning": "logging.Logger.warning",
        "log_info": "logging.Logger.info",
    }

    def setup_method(self):
        manager_full_module = self.manager.__module__ + "." + self.manager.__name__
        document_full_module = (
            self.manager.document.__module__ + "." + self.manager.document.__name__
        )

        # paths for document methods
        self.paths["document_get"] = document_full_module + ".get"
        self.paths["document_update"] = document_full_module + ".update"

        # paths for internal manager methods
        self.paths["create_index_document"] = (
            manager_full_module + ".create_index_document"
        )
        self.paths["add_to_index"] = manager_full_module + ".add_to_index"
        self.paths["update_in_index"] = manager_full_module + "._update_in_index"
        self.paths["remove_from_index"] = manager_full_module + ".remove_from_index"

    # @pytest.mark.django_db
    # def test_add_to_index_success(self):
    #     mock_document = MagicMock()
    #     instance = self.factory.create()
    #
    #     with patch(
    #         self.paths["create_index_document"], return_value=mock_document
    #     ) as mock_create_index_document, patch(
    #         self.paths["es_index_refresh"], return_value=None
    #     ) as mock_refresh, patch(
    #         self.paths["log_error"], return_value=None
    #     ) as mock_log_error:
    #         self.manager.add_to_index(instance)
    #
    #         mock_create_index_document.assert_called_once_with(instance)
    #         mock_document.save.assert_called_once()
    #         mock_refresh.assert_called_once()
    #         mock_log_error.assert_not_called()
    #
    # @pytest.mark.django_db
    # def test_add_failure_es_error(self):
    #     mock_document = MagicMock()
    #     mock_document.save.side_effect = ConnectionError("Whoops!")
    #     instance = self.factory.create()
    #
    #     with patch(
    #         self.paths["create_index_document"], return_value=mock_document
    #     ), patch(self.paths["log_error"], return_value=None) as mock_log_error:
    #         self.manager.add_to_index(instance)
    #         mock_log_error.assert_called()
    #
    # @pytest.mark.django_db
    # def test_update_in_index_success(self):
    #     mock_query, mock_search_obj = self.create_search_mocks()
    #     mock_existing_document = MagicMock()
    #     mock_new_document = MagicMock()
    #     mock_new_document.to_dict.return_value = {"test1": "value1"}
    #
    #     instance = self.factory.create()
    #
    #     with patch(
    #         self.paths["create_index_document"], return_value=mock_new_document
    #     ), patch(
    #         self.paths["es_search_init"], return_value=None
    #     ) as mock_search_init, patch(
    #         self.paths["es_search_params"], return_value=mock_search_obj
    #     ), patch(
    #         self.paths["document_get"], return_value=mock_existing_document
    #     ) as mock_get, patch(
    #         self.paths["es_index_refresh"], return_value=None
    #     ) as mock_refresh, patch(
    #         self.paths["log_error"], return_value=None
    #     ) as mock_log_error:
    #         self.manager.update_in_index(instance)
    #
    #         # assert searched the right index for the right id
    #         mock_search_init.assert_called_once_with(index=self.expected_index_name)
    #         mock_search_obj.query.assert_called_once_with(
    #             "match", document_id=instance.id
    #         )
    #         mock_query.execute.assert_called_once()
    #
    #         # assert updated the right index document with the right values
    #         mock_get.assert_called_once_with(id=TEST_SEARCH_INDEX_ID)
    #         mock_existing_document.update.assert_called_once_with(test1="value1")
    #
    #         # assert refreshed the index
    #         mock_refresh.assert_called_once()
    #
    #         mock_log_error.assert_not_called()
    #
    # @pytest.mark.django_db
    # def test_remove_from_index_success(self):
    #     mock_query, mock_search_obj = self.create_search_mocks()
    #     mock_existing_document = MagicMock()
    #
    #     instance = self.factory.create()
    #
    #     with patch(
    #         self.paths["es_search_init"], return_value=None
    #     ) as mock_search_init, patch(
    #         self.paths["es_search_params"], return_value=mock_search_obj
    #     ), patch(
    #         self.paths["document_get"], return_value=mock_existing_document
    #     ) as mock_get, patch(
    #         self.paths["es_index_refresh"], return_value=None
    #     ) as mock_refresh, patch(
    #         self.paths["log_error"], return_value=None
    #     ) as mock_log_error:
    #         self.manager.remove_from_index(instance.id)
    #
    #         # assert searched the right index for the right id
    #         mock_search_init.assert_called_once_with(index=self.expected_index_name)
    #         mock_search_obj.query.assert_called_once_with(
    #             "match", document_id=instance.id
    #         )
    #         mock_query.execute.assert_called_once()
    #
    #         # assert deleted the right index document with the right values
    #         mock_get.assert_called_once_with(id=TEST_SEARCH_INDEX_ID)
    #         mock_existing_document.delete.assert_called_once()
    #
    #         # assert refreshed the index
    #         mock_refresh.assert_called_once()
    #
    #         mock_log_error.assert_not_called()
    #
    # @pytest.mark.django_db
    # def test_update_failure_es_error(self):
    #     instance = self.factory.create()
    #
    #     with patch(
    #         self.paths["es_search_init"], side_effect=ConnectionError("Oh dear!")
    #     ), patch(self.paths["log_error"], return_value=None) as mock_log_error:
    #         self.manager.update_in_index(instance)
    #         mock_log_error.assert_called()
    #
    # @pytest.mark.django_db
    # def test_remove_failure_es_error(self):
    #     instance = self.factory.create()
    #
    #     with patch(
    #         self.paths["es_search_init"], side_effect=ConnectionError("Oh dear!")
    #     ), patch(self.paths["log_error"], return_value=None) as mock_log_error:
    #         self.manager.remove_from_index(instance.id)
    #         mock_log_error.assert_called()
    #
    # @pytest.mark.parametrize(
    #     "method",
    #     ["add_to_index", "update_in_index"],
    # )
    # @pytest.mark.django_db
    # def test_failure_surprise_exception(self, method):
    #     instance = self.factory.create()
    #
    #     with patch(self.paths["es_search_init"], return_value=None), patch(
    #         self.paths["create_index_document"], side_effect=Exception("Kaboom!")
    #     ), patch(self.paths["log_error"], return_value=None) as mock_log_error:
    #         m = getattr(self.manager, method)
    #         m(instance)
    #         mock_log_error.assert_called()
    #
    # @pytest.mark.django_db
    # def test_update_failure_search_result_not_found(self):
    #     mock_query, mock_search_obj = self.create_search_mocks()
    #     mock_query.execute.side_effect = NotFoundError()
    #
    #     instance = self.factory.create()
    #
    #     with patch(self.paths["es_search_init"], return_value=None), patch(
    #         self.paths["es_search_params"], return_value=mock_search_obj
    #     ), patch(self.paths["log_info"], return_value=None) as mock_log_info:
    #         self.manager.update_in_index(instance)
    #
    #         mock_log_info.assert_called()
    #
    # @pytest.mark.django_db
    # def test_remove_failure_search_result_not_found(self):
    #     mock_query, mock_search_obj = self.create_search_mocks()
    #     mock_query.execute.side_effect = NotFoundError()
    #
    #     instance = self.factory.create()
    #
    #     with patch(self.paths["es_search_init"], return_value=None), patch(
    #         self.paths["es_search_params"], return_value=mock_search_obj
    #     ), patch(self.paths["log_info"], return_value=None) as mock_log_info:
    #         self.manager.remove_from_index(instance.id)
    #
    #         mock_log_info.assert_called()
    #
    # @pytest.mark.django_db
    # def test_update_failure_index_doc_not_found(self):
    #     _, mock_search_obj = self.create_search_mocks()
    #
    #     instance = self.factory.create()
    #
    #     with patch(self.paths["es_search_init"], return_value=None), patch(
    #         self.paths["es_search_params"], return_value=mock_search_obj
    #     ), patch(
    #         self.paths["document_get"], side_effect=NotFoundError("Nice try!")
    #     ), patch(
    #         self.paths["log_info"], return_value=None
    #     ) as mock_log_info:
    #         self.manager.update_in_index(instance)
    #
    #         mock_log_info.assert_called()
    #
    # @pytest.mark.django_db
    # def test_remove_failure_index_doc_not_found(self):
    #     _, mock_search_obj = self.create_search_mocks()
    #
    #     instance = self.factory.create()
    #
    #     with patch(self.paths["es_search_init"], return_value=None), patch(
    #         self.paths["es_search_params"], return_value=mock_search_obj
    #     ), patch(
    #         self.paths["document_get"], side_effect=NotFoundError("Nice try!")
    #     ), patch(
    #         self.paths["log_info"], return_value=None
    #     ) as mock_log_info:
    #         self.manager.remove_from_index(instance.id)
    #
    #         mock_log_info.assert_called()
    #
    # @pytest.mark.django_db
    # def test_iterator(self):
    #     with patch(self.paths["create_index_document"]) as mock_create_index_doc:
    #         for _ in self.manager._iterator():
    #             continue
    #
    #         for instance in self.manager.model.objects.all():
    #             mock_create_index_doc.assert_any_call(instance)
    #
    # def create_indexable_document(self):
    #     """Subclasses should override if not all documents are indexed"""
    #     return self.factory.create()
    #
    # def create_non_indexable_document(self):
    #     """Subclasses should override if not all documents are indexed"""
    #     return None

    @pytest.mark.django_db
    def test_sync_in_index_new_good_document_is_added(self):
        mock_query, mock_search_obj = self.create_search_mocks()
        mock_query.execute.side_effect = (
            NotFoundError()
        )  # new document is not yet in the index

        instance = self.create_indexable_document()

        with patch(self.paths["es_search_init"], return_value=None), patch(
            self.paths["es_search_params"], return_value=mock_search_obj
        ), patch(self.paths["add_to_index"], return_value=None) as mock_add_to_index:
            self.manager.sync_in_index(instance.id)
            mock_add_to_index.assert_called_once_with(instance)

    # @pytest.mark.django_db
    # def test_sync_in_index_new_bad_document_is_skipped(self):
    #     mock_query, mock_search_obj = self.create_search_mocks()
    #     mock_query.execute.side_effect = (
    #         NotFoundError()
    #     )  # new document is not yet in the index
    #
    #     instance = self.create_non_indexable_document()
    #
    #     if instance:
    #         with patch(self.paths["es_search_init"], return_value=None), patch(
    #             self.paths["es_search_params"], return_value=mock_search_obj
    #         ), patch(
    #             self.paths["add_to_index"], return_value=None
    #         ) as mock_add_to_index, patch(
    #             self.paths["update_in_index"], return_value=None
    #         ) as mock_update_in_index:
    #             self.manager.sync_in_index(instance.id)
    #             mock_add_to_index.assert_not_called()
    #             mock_update_in_index.assert_not_called()
    #
    # @pytest.mark.django_db
    # def test_sync_in_index_edited_good_document_is_updated(self):
    #     _, mock_search_obj = self.create_search_mocks()
    #
    #     instance = self.create_indexable_document()
    #
    #     with patch(self.paths["es_search_init"], return_value=None), patch(
    #         self.paths["es_search_params"], return_value=mock_search_obj
    #     ), patch(
    #         self.paths["add_to_index"], return_value=None
    #     ) as mock_add_to_index, patch(
    #         self.paths["update_in_index"], return_value=None
    #     ) as mock_update_in_index, patch(
    #         self.paths["remove_from_index"], return_value=None
    #     ) as remove_from_index:
    #         self.manager.sync_in_index(instance.id)
    #
    #         mock_update_in_index.assert_called_once_with(instance)
    #         mock_add_to_index.assert_not_called()
    #         remove_from_index.assert_not_called()
    #
    # @pytest.mark.django_db
    # def test_sync_in_index_edited_bad_document_is_skipped(self):
    #     _, mock_search_obj = self.create_search_mocks()
    #
    #     instance = self.create_non_indexable_document()
    #
    #     if instance:
    #         with patch(self.paths["es_search_init"], return_value=None), patch(
    #             self.paths["es_search_params"], return_value=mock_search_obj
    #         ), patch(
    #             self.paths["add_to_index"], return_value=None
    #         ) as mock_add_to_index, patch(
    #             self.paths["update_in_index"], return_value=None
    #         ) as mock_update_in_index:
    #             self.manager.sync_in_index(instance.id)
    #
    #             mock_update_in_index.assert_not_called()
    #             mock_add_to_index.assert_not_called()
    #
    # @pytest.mark.django_db
    # def test_sync_in_index_edited_good_to_bad_document_is_removed(self):
    #     _, mock_search_obj = self.create_search_mocks()
    #     instance = self.create_non_indexable_document()
    #
    #     if instance:
    #         with patch(self.paths["es_search_init"], return_value=None), patch(
    #             self.paths["es_search_params"], return_value=mock_search_obj
    #         ), patch(
    #             self.paths["add_to_index"], return_value=None
    #         ) as mock_add_to_index, patch(
    #             self.paths["update_in_index"], return_value=None
    #         ) as mock_update_in_index, patch(
    #             self.paths["remove_from_index"], return_value=None
    #         ) as remove_from_index:
    #             self.manager.sync_in_index(instance.id)
    #
    #             remove_from_index.assert_called_once_with(instance.id)
    #             mock_update_in_index.assert_not_called()
    #             mock_add_to_index.assert_not_called()
    #
    # @pytest.mark.django_db
    # def test_sync_in_index_edited_bad_to_good_document_is_added(self):
    #     _, mock_search_obj = self.create_search_mocks()
    #
    #     instance = self.create_indexable_document()
    #
    #     with patch(self.paths["es_search_init"], return_value=None), patch(
    #         self.paths["es_search_params"], return_value=mock_search_obj
    #     ), patch(
    #         self.paths["add_to_index"], return_value=None
    #     ) as mock_add_to_index, patch(
    #         self.paths["update_in_index"], return_value=None
    #     ) as mock_update_in_index, patch(
    #         self.paths["remove_from_index"], return_value=None
    #     ) as remove_from_index:
    #         mock_update_in_index.side_effect = (
    #             NotFoundError()
    #         )  # document is not yet in the index
    #
    #         self.manager.sync_in_index(instance.id)
    #         mock_add_to_index.assert_called_once_with(instance)
    #         remove_from_index.assert_not_called()
    #
    # @pytest.mark.django_db
    # def test_sync_missing_instance_is_removed(self):
    #     _, mock_search_obj = self.create_search_mocks()
    #
    #     instance = self.create_indexable_document()
    #     instance_id = instance.id
    #     instance.delete()
    #
    #     with patch(self.paths["es_search_init"], return_value=None), patch(
    #         self.paths["es_search_params"], return_value=mock_search_obj
    #     ), patch(self.paths["log_warning"], return_value=None), patch(
    #         self.paths["remove_from_index"], return_value=None
    #     ) as mock_remove_from_index:
    #         self.manager.sync_in_index(instance_id)
    #         mock_remove_from_index.assert_called_once_with(instance_id)

    def create_search_mocks(self):
        mock_query = MagicMock()
        mock_query.execute.return_value = {
            "hits": {"hits": [{"_id": TEST_SEARCH_INDEX_ID}]}
        }
        mock_search_obj = MagicMock()
        mock_search_obj.query.return_value = mock_query
        return mock_query, mock_search_obj

    def get_mock_document_with_es_error(self):
        mock_document = MagicMock()
        mock_document.save.side_effect = ConnectionError("Uh oh!")
        return mock_document


class BaseSignalTest:
    """
    Tests for basic indexing signal cases:
    * all instances are indexed (no criteria)
    """

    manager = None
    factory = None

    @pytest.fixture
    def mock_index_methods(self, mocker):
        return {
            "mock_sync": mocker.patch.object(self.manager, "sync_in_index"),
            "mock_remove": mocker.patch.object(self.manager, "remove_from_index"),
        }

    @pytest.mark.django_db
    def test_new_instance_is_synced(self, mock_index_methods):
        instance = self.factory.create()

        mock_index_methods["mock_sync"].assert_called_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_edited_instance_is_synced(self, mock_index_methods):
        instance = self.factory.create()
        mock_index_methods["mock_sync"].reset_mock()

        instance.title = "New Title"
        instance.save()

        mock_index_methods["mock_sync"].assert_called_once_with(instance.id)
        mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_deleted_instance_is_removed(self, mock_index_methods):
        instance = self.factory.create()
        instance_id = instance.id
        mock_index_methods["mock_sync"].reset_mock()

        instance.delete()

        mock_index_methods["mock_remove"].assert_called_once_with(instance_id)
        mock_index_methods["mock_sync"].assert_not_called()


class BaseRelatedInstanceSignalTest(BaseSignalTest):
    """
    Tests for basic indexing signal cases and:
    * one-to-many related models are included with the indexed content
      (e.g., Songs and Lyrics, but not DictionaryEntries and Categories)
    """

    related_factories = []

    def create_all_related_instances(self, instance):
        for related_factory in self.related_factories:
            self.create_related_instance(related_factory, instance)

    def create_related_instance(self, related_factory, instance):
        raise NotImplementedError()

    def edit_related_instance(self, related_instance):
        related_instance.text = "New text"
        related_instance.save()

    @pytest.mark.django_db
    def test_deleted_instance_with_related_instance_is_removed(
        self, mock_index_methods
    ):
        instance = self.factory.create()
        instance_id = instance.id
        self.create_all_related_instances(instance)
        mock_index_methods["mock_sync"].reset_mock()

        instance.delete()

        mock_index_methods["mock_remove"].assert_called_once_with(instance_id)

    @pytest.mark.django_db
    def test_new_related_instance_main_instance_is_synced(self, mock_index_methods):
        for related_factory in self.related_factories:
            instance = self.factory.create()
            mock_index_methods["mock_sync"].reset_mock()
            self.create_related_instance(related_factory, instance)

            mock_index_methods["mock_sync"].assert_called_with(instance.id)
            mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_edited_related_instance_main_instance_is_synced(self, mock_index_methods):
        for related_factory in self.related_factories:
            instance = self.factory.create()
            related_instance = self.create_related_instance(related_factory, instance)
            mock_index_methods["mock_sync"].reset_mock()

            self.edit_related_instance(related_instance)

            mock_index_methods["mock_sync"].assert_called_once_with(instance.id)
            mock_index_methods["mock_remove"].assert_not_called()

    @pytest.mark.django_db
    def test_deleted_related_instance_main_instance_is_synced(self, mock_index_methods):
        for related_factory in self.related_factories:
            instance = self.factory.create()
            instance_id = instance.id
            related_instance = self.create_related_instance(related_factory, instance)
            mock_index_methods["mock_sync"].reset_mock()

            related_instance.delete()

            mock_index_methods["mock_sync"].assert_called_once_with(instance_id)
            mock_index_methods["mock_remove"].assert_not_called()
