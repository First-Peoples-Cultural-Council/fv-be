from unittest.mock import patch

import pytest

from backend.models.constants import Visibility
from backend.search.indexing import LanguageIndexManager
from backend.search.utils.constants import ELASTICSEARCH_LANGUAGE_INDEX
from backend.tests import factories
from backend.tests.test_search_indexing.test_index_manager import BaseIndexManagerTest


class TestLanguageIndexManager(BaseIndexManagerTest):
    manager = LanguageIndexManager
    factory = factories.LanguageFactory
    expected_index_name = ELASTICSEARCH_LANGUAGE_INDEX

    @pytest.mark.skip("Replaced with several tests for custom iteration")
    def test_iterator(self):
        """See other more specific tests instead:
        - test_iterator_skips_languages_without_sites
        - test_iterator_skips_languages_with_only_team_sites
        """
        pass

    @pytest.mark.django_db
    def test_iterator_skips_languages_without_sites(self):
        with patch(self.paths["create_index_document"]) as mock_create_index_doc:
            factories.LanguageFactory.create()  # language with no sites

            language1 = factories.LanguageFactory.create()
            factories.SiteFactory.create(
                language=language1, visibility=Visibility.MEMBERS
            )

            for _ in self.manager._iterator():
                continue

            # assert adds all languages with sites
            mock_create_index_doc.assert_any_call(language1)

            # assert does not add other (empty) languages
            assert mock_create_index_doc.call_count == 1

    @pytest.mark.django_db
    def test_iterator_skips_languages_with_only_team_sites(self):
        with patch(self.paths["create_index_document"]) as mock_create_index_doc:
            language1 = (
                factories.LanguageFactory.create()
            )  # language with only private sites
            factories.SiteFactory.create(language=language1, visibility=Visibility.TEAM)

            language2 = factories.LanguageFactory.create()
            factories.SiteFactory.create(language=language2, visibility=Visibility.TEAM)
            factories.SiteFactory.create(
                language=language2, visibility=Visibility.PUBLIC
            )

            language3 = factories.LanguageFactory.create()
            factories.SiteFactory.create(
                language=language3, visibility=Visibility.MEMBERS
            )

            for _ in self.manager._iterator():
                continue

            # assert adds all languages with visible sites
            mock_create_index_doc.assert_any_call(language2)
            mock_create_index_doc.assert_any_call(language3)

            # assert does not add other (empty) languages
            assert mock_create_index_doc.call_count == 2

    # @pytest.mark.django_db
    # def test_iterator_includes_visible_sites_with_no_language(self):
    #     with patch(
    #         "backend.search.indexing.LanguageIndexManager.create_site_index_document"
    #     ) as mock_create_index_doc:
    #         factories.SiteFactory.create(language=None, visibility=Visibility.TEAM)
    #         member_site = factories.SiteFactory.create(
    #             language=None, visibility=Visibility.MEMBERS
    #         )
    #         public_site = factories.SiteFactory.create(
    #             language=None, visibility=Visibility.PUBLIC
    #         )
    #
    #         for _ in self.manager._iterator():
    #             continue
    #
    #         # assert adds all languages with visible sites
    #         mock_create_index_doc.assert_any_call(member_site)
    #         mock_create_index_doc.assert_any_call(public_site)
    #
    #         # assert does not add other (empty) languages
    #         assert mock_create_index_doc.call_count == 2

    @pytest.mark.django_db
    def test_create_document_with_language_fields(self):
        language = factories.LanguageFactory.create(
            alternate_names="alt name 1 , alt name 2,altname 3",
            community_keywords="keyword 1, keyword 2",
            language_code="abc,def, efg",
        )
        language_doc = LanguageIndexManager.create_index_document(language)

        assert language_doc.document_id == str(language.id)
        assert language_doc.document_type == "Language"
        assert language_doc.language_name == language.title

        self.assert_list(
            ["abc", "def", "efg"],
            language_doc.language_code,
        )
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
        site1 = factories.SiteFactory.create(
            language=language, visibility=Visibility.PUBLIC
        )
        site2 = factories.SiteFactory.create(
            language=language, visibility=Visibility.MEMBERS
        )
        factories.SiteFactory.create(language=language, visibility=Visibility.TEAM)

        language_doc = LanguageIndexManager.create_index_document(language)

        self.assert_list([site1.title, site2.title], language_doc.site_names)
        self.assert_list([site1.slug, site2.slug], language_doc.site_slugs)

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
