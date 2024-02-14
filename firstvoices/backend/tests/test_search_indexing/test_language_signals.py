import pytest

from backend.search.indexing.language_index import (
    LanguageDocumentManager,
    SiteDocumentManager,
)
from backend.tests import factories


@pytest.fixture
def mock_index_methods(mocker):
    return {
        "mock_sync_language": mocker.patch.object(
            LanguageDocumentManager, "sync_in_index"
        ),
        "mock_remove_language": mocker.patch.object(
            LanguageDocumentManager, "remove_from_index"
        ),
        "mock_sync_site": mocker.patch.object(SiteDocumentManager, "sync_in_index"),
        "mock_remove_site": mocker.patch.object(
            SiteDocumentManager, "remove_from_index"
        ),
    }


class TestLanguageIndexingSignals:
    @pytest.mark.django_db
    def test_new_language_family_is_skipped(self, mock_index_methods):
        factories.LanguageFamilyFactory.create()

        mock_index_methods["mock_sync_language"].assert_not_called()
        mock_index_methods["mock_remove_language"].assert_not_called()
        mock_index_methods["mock_sync_site"].assert_not_called()
        mock_index_methods["mock_remove_site"].assert_not_called()

    @pytest.mark.django_db
    def test_edited_language_family_related_languages_are_synced(
        self, mock_index_methods
    ):
        family = factories.LanguageFamilyFactory.create()
        factories.LanguageFactory.create(language_family=family)
        factories.LanguageFactory.create(language_family=family)
        factories.LanguageFactory.create()
        mock_index_methods["mock_sync_language"].reset_mock()

        family.title = "New Family Title"
        family.save()

        assert mock_index_methods["mock_sync_language"].call_count == 2
        mock_index_methods["mock_remove_language"].assert_not_called()
        mock_index_methods["mock_sync_site"].assert_not_called()
        mock_index_methods["mock_remove_site"].assert_not_called()

    @pytest.mark.django_db
    def test_new_language_is_synced(self, mock_index_methods):
        language = factories.LanguageFactory.create()

        mock_index_methods["mock_sync_language"].assert_called_once_with(language.id)
        mock_index_methods["mock_remove_language"].assert_not_called()
        mock_index_methods["mock_sync_site"].assert_not_called()
        mock_index_methods["mock_remove_site"].assert_not_called()

    @pytest.mark.django_db
    def test_edited_language_is_synced(self, mock_index_methods):
        language = factories.LanguageFactory.create()
        mock_index_methods["mock_sync_language"].reset_mock()

        language.title = "New title"
        language.save()
        mock_index_methods["mock_sync_language"].assert_called_once_with(language.id)
        mock_index_methods["mock_remove_language"].assert_not_called()
        mock_index_methods["mock_sync_site"].assert_not_called()
        mock_index_methods["mock_remove_site"].assert_not_called()

    @pytest.mark.django_db
    def test_deleted_language_is_removed(self, mock_index_methods):
        language = factories.LanguageFactory.create()
        language_id = language.id
        language.delete()
        mock_index_methods["mock_remove_language"].assert_called_once_with(language_id)

    @pytest.mark.django_db
    def test_deleted_language_related_sites_are_synced(self, mock_index_methods):
        language = factories.LanguageFactory.create()
        factories.SiteFactory.create(language=language)
        factories.SiteFactory.create(language=language)
        factories.SiteFactory.create(language=None)
        mock_index_methods["mock_sync_language"].reset_mock()
        mock_index_methods["mock_sync_site"].reset_mock()

        language.delete()
        assert mock_index_methods["mock_sync_site"].call_count == 2


class TestSiteIndexingSignals:
    @pytest.mark.django_db
    def test_new_site_without_language_is_synced(self, mock_index_methods):
        site = factories.SiteFactory.create(language=None)
        mock_index_methods["mock_sync_site"].assert_called_once_with(site.id)

    @pytest.mark.django_db
    def test_new_site_with_language_is_synced(self, mock_index_methods):
        language = factories.LanguageFactory.create()
        mock_index_methods["mock_sync_site"].reset_mock()

        site = factories.SiteFactory.create(language=language)
        mock_index_methods["mock_sync_site"].assert_called_once_with(site.id)

    @pytest.mark.django_db
    def test_new_site_related_language_is_synced(self, mock_index_methods):
        language = factories.LanguageFactory.create()
        mock_index_methods["mock_sync_language"].reset_mock()

        factories.SiteFactory.create(language=language)
        mock_index_methods["mock_sync_language"].assert_called_once_with(language.id)

    @pytest.mark.django_db
    def test_edited_site_is_synced(self, mock_index_methods):
        site = factories.SiteFactory.create()
        mock_index_methods["mock_sync_site"].reset_mock()

        site.title = "New Title"
        site.save()
        mock_index_methods["mock_sync_site"].assert_called_once_with(site.id)

    @pytest.mark.django_db
    def test_edited_site_related_languages_are_synced(self, mock_index_methods):
        language1 = factories.LanguageFactory.create()
        language2 = factories.LanguageFactory.create()
        site = factories.SiteFactory.create(language=language1)
        mock_index_methods["mock_sync_language"].reset_mock()
        mock_index_methods["mock_sync_site"].reset_mock()

        site.language = language2
        site.save()
        assert mock_index_methods["mock_sync_language"].call_count == 2

    @pytest.mark.django_db
    def test_deleted_site_is_removed(self, mock_index_methods):
        site = factories.SiteFactory.create()
        site_id = site.id
        site.delete()
        mock_index_methods["mock_remove_site"].assert_called_once_with(site_id)

    @pytest.mark.django_db
    def test_deleted_site_related_language_is_synced(self, mock_index_methods):
        language = factories.LanguageFactory.create()
        site = factories.SiteFactory.create(language=language)
        mock_index_methods["mock_sync_language"].reset_mock()

        site.delete()
        mock_index_methods["mock_sync_language"].assert_called_once_with(language.id)
