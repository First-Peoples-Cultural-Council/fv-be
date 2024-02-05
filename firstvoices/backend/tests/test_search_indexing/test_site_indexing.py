from unittest.mock import patch

import pytest

from backend.models.constants import Visibility
from backend.search.indexing import SiteLanguageIndexManager
from backend.search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX
from backend.tests import factories
from backend.tests.test_search_indexing.test_index_manager import BaseIndexManagerTest


class TestSiteLanguageIndexManager(BaseIndexManagerTest):
    manager = SiteLanguageIndexManager
    factory = factories.SiteFactory
    expected_index_name = ELASTICSEARCH_LANGUAGE_INDEX

    @pytest.mark.skip("Replaced with several tests for custom iteration")
    def test_iterator(self):
        """See other more specific tests instead:
        - test_iterator_skips_languages_without_sites
        - test_iterator_skips_languages_with_only_team_sites
        """
        pass

    @pytest.mark.django_db
    def test_iterator_only_includes_sites_with_no_language(self):
        with patch(
            "backend.search.indexing.SiteLanguageIndexManager.create_index_document"
        ) as mock_create_index_doc:
            language = factories.LanguageFactory.create()
            factories.SiteFactory.create(
                language=language, visibility=Visibility.PUBLIC
            )

            site_with_no_language = factories.SiteFactory.create(
                language=None, visibility=Visibility.PUBLIC
            )

            for _ in self.manager._iterator():
                continue

            mock_create_index_doc.assert_any_call(site_with_no_language)
            assert mock_create_index_doc.call_count == 1

    @pytest.mark.django_db
    def test_iterator_skips_team_sites(self):
        with patch(
            "backend.search.indexing.SiteLanguageIndexManager.create_index_document"
        ) as mock_create_index_doc:
            site_public = factories.SiteFactory.create(
                language=None, visibility=Visibility.PUBLIC
            )
            site_member = factories.SiteFactory.create(
                language=None, visibility=Visibility.MEMBERS
            )
            factories.SiteFactory.create(language=None, visibility=Visibility.TEAM)

            for _ in self.manager._iterator():
                continue

            mock_create_index_doc.assert_any_call(site_public)
            mock_create_index_doc.assert_any_call(site_member)
            assert mock_create_index_doc.call_count == 2

    @pytest.mark.django_db
    def test_iterator_skips_hidden_sites(self):
        with patch(
            "backend.search.indexing.SiteLanguageIndexManager.create_index_document"
        ) as mock_create_index_doc:
            site_public = factories.SiteFactory.create(
                language=None, visibility=Visibility.PUBLIC, is_hidden=False
            )
            factories.SiteFactory.create(
                language=None, visibility=Visibility.PUBLIC, is_hidden=True
            )

            for _ in self.manager._iterator():
                continue

            mock_create_index_doc.assert_any_call(site_public)
            assert mock_create_index_doc.call_count == 1

    @pytest.mark.django_db
    def test_create_document_with_site_fields(self):
        site = factories.SiteFactory.create(language=None, visibility=Visibility.PUBLIC)

        index_doc = SiteLanguageIndexManager.create_index_document(site)

        assert index_doc.document_id == str(site.id)
        assert index_doc.document_type == "Site"
        assert index_doc.site_names == site.title
        assert index_doc.site_slugs == site.slug
