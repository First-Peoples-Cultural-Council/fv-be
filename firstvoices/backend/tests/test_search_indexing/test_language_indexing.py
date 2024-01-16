from unittest.mock import patch

import pytest

from backend.models.sites import Language
from backend.search.indexing import LanguageIndexManager
from backend.search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX
from backend.tests import factories
from backend.tests.test_search_indexing.test_index_manager import BaseIndexManagerTest


class TestLanguageIndexManager(BaseIndexManagerTest):
    manager = LanguageIndexManager
    factory = factories.LanguageFactory
    expected_index_name = ELASTICSEARCH_LANGUAGE_INDEX

    @pytest.mark.django_db
    def test_iterator(self):
        """Override to test that only languages containing sites are indexed"""
        with patch(self.paths["create_index_document"]) as mock_create_index_doc:
            for _ in self.manager._iterator():
                continue

            # assert adds all languages with sites
            languages_with_sites = Language.objects.all().exclude(sites=None)
            for instance in languages_with_sites:
                mock_create_index_doc.assert_any_call(instance)

            # assert does not add empty languages
            assert mock_create_index_doc.call_count == languages_with_sites.count()

    @pytest.mark.django_db
    def test_create_document_with_language_fields(self):
        language = factories.LanguageFactory.create(
            alternate_names="alt name 1 , alt name 2,altname 3",
            community_keywords="keyword 1, keyword 2",
        )
        language_doc = LanguageIndexManager.create_index_document(language)

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
    def test_create_document_with_site_fields(self):
        language = factories.LanguageFactory.create()
        site1 = factories.SiteFactory.create(language=language)
        site2 = factories.SiteFactory.create(language=language)
        site3 = factories.SiteFactory.create(language=language)

        language_doc = LanguageIndexManager.create_index_document(language)

        self.assert_list(
            [site1.title, site2.title, site3.title], language_doc.site_names
        )
        self.assert_list([site1.slug, site2.slug, site3.slug], language_doc.site_slugs)

    @pytest.mark.django_db
    def test_create_document_with_language_family_fields(self):
        language_family = factories.LanguageFamilyFactory.create(
            alternate_names="family 1 , alternate 2,alt.fam.3"
        )
        language = factories.LanguageFactory.create(language_family=language_family)

        language_doc = LanguageIndexManager.create_index_document(language)

        assert language_doc.language_family_name == language_family.title
        self.assert_list(
            ["family 1", "alternate 2", "alt.fam.3"],
            language_doc.language_family_alternate_names,
        )

    def assert_list(self, expected_list, actual_list):
        assert len(expected_list) == len(actual_list)

        for i, item in enumerate(expected_list):
            assert item in actual_list
