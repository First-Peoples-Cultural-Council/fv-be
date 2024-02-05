from unittest.mock import patch

import pytest

from backend.models.sites import Language, LanguageFamily
from backend.tests import factories


@pytest.fixture
def mock_add_to_index():
    with (
        patch(
            "backend.search.indexing.LanguageIndexManager.add_to_index"
        ) as mock_add_to_index,
    ):
        mock_add_to_index.return_value = None
        yield mock_add_to_index


@pytest.fixture
def mock_update_in_index():
    with (
        patch(
            "backend.search.indexing.LanguageIndexManager.update_in_index"
        ) as mock_update_in_index,
    ):
        mock_update_in_index.return_value = None
        yield mock_update_in_index


@pytest.fixture
def mock_remove_from_index():
    with (
        patch(
            "backend.search.indexing.LanguageIndexManager.remove_from_index"
        ) as mock_remove_from_index,
    ):
        mock_remove_from_index.return_value = None
        yield mock_remove_from_index


class TestLanguageIndexingSignals:
    @pytest.fixture()
    def disable_celery(self, settings):
        # Sets the celery tasks to run synchronously for testing
        settings.CELERY_TASK_ALWAYS_EAGER = True

    @pytest.mark.django_db
    def test_new_language_is_added(self, mock_add_to_index):
        family = LanguageFamily.objects.all().first()
        language = Language.objects.create(title="New Language", language_family=family)
        language.save()

        mock_add_to_index.assert_called_with(language)

    @pytest.mark.django_db
    def test_deleted_language_is_removed(
        self, mock_add_to_index, mock_remove_from_index
    ):
        language = factories.LanguageFactory.create()
        mock_add_to_index.assert_called_with(language)
        mock_remove_from_index.assert_not_called()

        language.delete()
        mock_remove_from_index.assert_called_with(language)

    def test_updated_language_is_updated(self, mock_add_to_index, mock_update_in_index):
        language = factories.LanguageFactory.create()
        mock_add_to_index.assert_called_with(language)
        mock_update_in_index.assert_not_called()

        language.language_code = "test"
        language.save()
        mock_update_in_index.assert_called_with(language)

    def test_add_first_public_site_adds_language(self):
        pass

    def test_add_second_public_site_updates_language(self):
        pass

    def test_remove_last_public_site_removes_language(self):
        pass

    def test_remove_one_public_site_updates_language(self):
        pass

    def test_update_first_site_to_public_adds_language(self):
        pass

    def test_update_second_site_to_public_updates_language(self):
        pass

    def test_update_last_site_to_team_removes_language(self):
        pass

    def test_update_one_site_to_team_updates_language(self):
        pass

    def test_add_site_with_no_language(self):
        pass

    def test_update_site_with_no_language(self):
        pass

    def test_update_site_to_add_language(self):
        pass

    def test_update_site_to_remove_language(self):
        pass

    def test_delete_site_with_no_language(self):
        pass
