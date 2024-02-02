from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl import Search

from backend.pagination import SearchPageNumberPagination


class SearchMocksMixin:
    """
    Mocking for search operations.
    """

    @pytest.fixture
    def mock_get_page_size(self, mocker):
        return mocker.patch.object(
            SearchPageNumberPagination, "get_page_size", new_callable=MagicMock
        )

    @pytest.fixture
    def mock_search_query_execute(self, mocker):
        return mocker.patch.object(Search, "execute", new_callable=MagicMock)
