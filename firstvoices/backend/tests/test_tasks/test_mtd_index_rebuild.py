import pytest

from backend.models import Category, DictionaryEntry, Site, Translation
from backend.models.constants import AppRole, Visibility
from backend.models.media import Audio, Image
from backend.tests.factories import get_app_admin


@pytest.mark.django_db
class TestMtdIndexRebuild:
    # Test if the mtd index rebuild is triggered only when required
    # Mocking rebuild_mtd_index method from mtd_signals.py
    # To also test the signals functionality, using models instead of test factories

    def setup_method(self):
        self.admin_user = get_app_admin(AppRole.STAFF)
        self.site = Site(
            title="test_site",
            slug="test_site",
            visibility=Visibility.PUBLIC,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        self.site.save()

    def test_public_entry_updated(self, mocker):
        mocked_func = mocker.patch(
            "backend.models.signals.mtd_signals.rebuild_mtd_index"
        )
        entry = DictionaryEntry(
            title="test_entry", site=self.site, visibility=Visibility.PUBLIC
        )
        entry.save()

        assert mocked_func.call_count == 1
        mocked_func.assert_called_once_with(self.site.slug)

        entry.title = "Entry updated"
        entry.save()

        assert mocked_func.call_count == 2
        mocked_func.assert_called_with(self.site.slug)

        # Deleting entry
        entry.delete()
        assert mocked_func.call_count == 3
        mocked_func.assert_called_with(self.site.slug)

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    def test_non_public_entry_updated(self, mocker, visibility):
        mocked_func = mocker.patch(
            "backend.models.signals.mtd_signals.rebuild_mtd_index"
        )
        entry = DictionaryEntry(site=self.site, visibility=visibility)
        entry.save()

        # mtd index rebuild should not be triggered
        assert mocked_func.call_count == 0

        entry.title = "Entry updated"
        entry.save()

        assert mocked_func.call_count == 0

        # Deleting entry
        entry.delete()
        assert mocked_func.call_count == 0

    def test_category_updated_public_entry(self, mocker):
        mocked_func = mocker.patch(
            "backend.models.signals.mtd_signals.rebuild_mtd_index"
        )
        category = Category(
            title="test_category",
            site=self.site,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        category.save()
        entry = DictionaryEntry(site=self.site, visibility=Visibility.PUBLIC)
        entry.categories.add(category)
        translation = Translation(text="Test Translation", dictionary_entry=entry)
        translation.save()

        entry.save()
        assert mocked_func.call_count == 1

        category.title = "Category title updated"
        category.save()
        assert mocked_func.call_count == 2
        mocked_func.assert_called_with(self.site.slug)

    def test_category_updated_public_entry_no_translation(self, mocker):
        mocked_func = mocker.patch(
            "backend.models.signals.mtd_signals.rebuild_mtd_index"
        )
        category = Category(
            title="test_category",
            site=self.site,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        category.save()
        entry = DictionaryEntry(site=self.site, visibility=Visibility.PUBLIC)
        entry.categories.add(category)

        entry.save()
        assert mocked_func.call_count == 1

        category.title = "Category title updated"
        category.save()

        # Should not trigger rebuild of index
        assert mocked_func.call_count == 1
        mocked_func.assert_called_with(self.site.slug)

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    def test_category_updated_non_public_entry(self, mocker, visibility):
        mocked_func = mocker.patch(
            "backend.models.signals.mtd_signals.rebuild_mtd_index"
        )
        category = Category(
            title="test_category",
            site=self.site,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        category.save()
        entry = DictionaryEntry(site=self.site, visibility=visibility)
        entry.categories.add(category)
        translation = Translation(text="Test Translation", dictionary_entry=entry)
        translation.save()

        entry.save()
        assert mocked_func.call_count == 0

        category.title = "Category title updated"
        category.save()

        # Should not trigger the rebuild of index
        assert mocked_func.call_count == 0

    def test_related_image_updated(self, mocker):
        mocked_func = mocker.patch(
            "backend.models.signals.mtd_signals.rebuild_mtd_index"
        )
        image = Image(title="test image", site=self.site)
        image.save()

        entry = DictionaryEntry(site=self.site, visibility=Visibility.PUBLIC)
        entry.save()

        assert mocked_func.call_count == 1

        entry.related_images.add(image)
        entry.save()

        assert mocked_func.call_count == 2

        entry.related_images.remove(image)
        entry.save()

        assert mocked_func.call_count == 3
        mocked_func.assert_called_with(self.site.slug)

    def test_related_audio_updated(self, mocker):
        mocked_func = mocker.patch(
            "backend.models.signals.mtd_signals.rebuild_mtd_index"
        )
        audio = Audio(title="test audio", site=self.site)
        audio.save()

        entry = DictionaryEntry(site=self.site, visibility=Visibility.PUBLIC)
        entry.save()

        assert mocked_func.call_count == 1

        entry.related_audio.add(audio)
        entry.save()

        assert mocked_func.call_count == 2

        entry.related_audio.remove(audio)
        entry.save()

        assert mocked_func.call_count == 3
        mocked_func.assert_called_with(self.site.slug)
