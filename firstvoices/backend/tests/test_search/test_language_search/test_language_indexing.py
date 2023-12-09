from unittest.mock import MagicMock, patch

import pytest
from elasticsearch.exceptions import ConnectionError, NotFoundError

from backend.search.indexing.language_indexing import (
    add_to_index,
    create_index_document,
    remove_from_index,
    update_in_index,
)
from backend.search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX
from backend.tests import factories


class TestCreateLanguageDocument:
    @pytest.mark.django_db
    def test_has_language_fields(self):
        language = factories.LanguageFactory.create(
            alternate_names="alt name 1 , alt name 2,altname 3",
            community_keywords="keyword 1, keyword 2",
        )
        language_doc = create_index_document(language)

        assert language_doc.language_name == language.title
        assert language_doc.language_code == language.language_code

        self.assert_list(
            ["alt name 1", "alt name 2", "altname 3"],
            language_doc.language_alternate_names,
        )
        self.assert_list(
            ["keyword 1", "keyword 2"], language_doc.language_community_keywords
        )

    @pytest.mark.django_db
    def test_has_site_fields(self):
        language = factories.LanguageFactory.create()
        site1 = factories.SiteFactory.create(language=language)
        site2 = factories.SiteFactory.create(language=language)
        site3 = factories.SiteFactory.create(language=language)

        language_doc = create_index_document(language)

        self.assert_list(
            [site1.title, site2.title, site3.title], language_doc.site_names
        )
        self.assert_list([site1.slug, site2.slug, site3.slug], language_doc.site_slugs)

    @pytest.mark.django_db
    def test_has_language_family_fields(self):
        language_family = factories.LanguageFamilyFactory.create(
            alternate_names="family 1 , alternate 2,alt.fam.3"
        )
        language = factories.LanguageFactory.create(language_family=language_family)

        language_doc = create_index_document(language)

        assert language_doc.language_family_name == language_family.title
        self.assert_list(
            ["family 1", "alternate 2", "alt.fam.3"],
            language_doc.language_family_alternate_names,
        )

    def assert_list(self, expected_list, actual_list):
        assert len(expected_list) == len(actual_list)

        for i, item in enumerate(expected_list):
            assert item in actual_list


class TestLanguageIndexing:
    paths = {
        "create_index_document": "backend.search.indexing.language_indexing.create_index_document",
        "refresh": "elasticsearch_dsl.index.Index.refresh",
        "document_get": "backend.search.documents.language_document.LanguageDocument.get",
        "document_update": "backend.search.documents.language_document.LanguageDocument.update",
        "search_init": "elasticsearch_dsl.search.Search.__init__",
        "search_params": "elasticsearch_dsl.search.Search.params",
        "log_error": "logging.Logger.error",
        "log_warning": "logging.Logger.warning",
    }

    @pytest.mark.django_db
    def test_add_to_index_success(self):
        mock_document = MagicMock()
        language = factories.LanguageFactory.create()

        with patch(
            self.paths["create_index_document"], return_value=mock_document
        ) as mock_create_index_document, patch(
            self.paths["refresh"], return_value=None
        ) as mock_refresh, patch(
            self.paths["log_error"], return_value=None
        ) as mock_log_error:
            add_to_index(language=language)

            mock_create_index_document.assert_called_once_with(language)
            mock_document.save.assert_called_once()
            mock_refresh.assert_called_once()
            mock_log_error.assert_not_called()

    @pytest.mark.django_db
    def test_update_in_index_success(self):
        mock_query, mock_search_obj = self.create_search_mocks()
        mock_existing_document = MagicMock()
        mock_new_document = MagicMock()
        mock_new_document.to_dict.return_value = {"test1": "value1"}

        language = factories.LanguageFactory.create()

        with patch(
            self.paths["create_index_document"], return_value=mock_new_document
        ), patch(
            self.paths["search_init"], return_value=None
        ) as mock_search_init, patch(
            self.paths["search_params"], return_value=mock_search_obj
        ), patch(
            self.paths["document_get"], return_value=mock_existing_document
        ) as mock_get, patch(
            self.paths["refresh"], return_value=None
        ) as mock_refresh, patch(
            self.paths["log_error"], return_value=None
        ) as mock_log_error:
            update_in_index(language=language)

            # assert searched the right index for the right id
            mock_search_init.assert_called_once_with(index=ELASTICSEARCH_LANGUAGE_INDEX)
            mock_search_obj.query.assert_called_once_with(
                "match", document_id=language.id
            )
            mock_query.execute.assert_called_once()

            # assert updated the right index document with the right values
            mock_get.assert_called_once_with(id="test search index id")
            mock_existing_document.update.assert_called_once_with(test1="value1")

            # assert refreshed the index
            mock_refresh.assert_called_once()

            mock_log_error.assert_not_called()

    @pytest.mark.django_db
    def test_remove_from_index_success(self):
        mock_query, mock_search_obj = self.create_search_mocks()
        mock_existing_document = MagicMock()

        language = factories.LanguageFactory.create()

        with patch(
            self.paths["search_init"], return_value=None
        ) as mock_search_init, patch(
            self.paths["search_params"], return_value=mock_search_obj
        ), patch(
            self.paths["document_get"], return_value=mock_existing_document
        ) as mock_get, patch(
            self.paths["refresh"], return_value=None
        ) as mock_refresh, patch(
            self.paths["log_error"], return_value=None
        ) as mock_log_error:
            remove_from_index(language=language)

            # assert searched the right index for the right id
            mock_search_init.assert_called_once_with(index=ELASTICSEARCH_LANGUAGE_INDEX)
            mock_search_obj.query.assert_called_once_with(
                "match", document_id=language.id
            )
            mock_query.execute.assert_called_once()

            # assert deleted the right index document with the right values
            mock_get.assert_called_once_with(id="test search index id")
            mock_existing_document.delete.assert_called_once()

            # assert refreshed the index
            mock_refresh.assert_called_once()

            mock_log_error.assert_not_called()

    @pytest.mark.parametrize(
        "method", [add_to_index, update_in_index, remove_from_index]
    )
    @pytest.mark.django_db
    def test_failure_es_error(self, method):
        language = factories.LanguageFactory.create()

        with patch(
            self.paths["search_init"], side_effect=ConnectionError("Nice try!")
        ), patch(self.paths["log_error"], return_value=None) as mock_log_error:
            method(language=language)
            mock_log_error.assert_called()

    @pytest.mark.parametrize("method", [update_in_index, remove_from_index])
    @pytest.mark.django_db
    def test_failure_search_result_not_found(self, method):
        mock_query, mock_search_obj = self.create_search_mocks()
        mock_query.execute.side_effect = NotFoundError("Oopsie!")

        language = factories.LanguageFactory.create()

        with patch(self.paths["search_init"], return_value=None), patch(
            self.paths["search_params"], return_value=mock_search_obj
        ), patch(self.paths["log_warning"], return_value=None) as mock_log_warning:
            method(language=language)

            mock_log_warning.assert_called()

    @pytest.mark.parametrize("method", [update_in_index, remove_from_index])
    @pytest.mark.django_db
    def test_failure_index_doc_not_found(self, method):
        _, mock_search_obj = self.create_search_mocks()

        language = factories.LanguageFactory.create()

        with patch(self.paths["search_init"], return_value=None), patch(
            self.paths["search_params"], return_value=mock_search_obj
        ), patch(
            self.paths["document_get"], side_effect=NotFoundError("Nice try!")
        ), patch(
            self.paths["log_warning"], return_value=None
        ) as mock_log_warning:
            method(language=language)

            mock_log_warning.assert_called()

    def create_search_mocks(self):
        mock_query = MagicMock()
        mock_query.execute.return_value = {
            "hits": {"hits": [{"_id": "test search index id"}]}
        }
        mock_search_obj = MagicMock()
        mock_search_obj.query.return_value = mock_query
        return mock_query, mock_search_obj

    def get_mock_document_with_es_error(self):
        mock_document = MagicMock()
        mock_document.save.side_effect = ConnectionError("Uh oh!")
        return mock_document
