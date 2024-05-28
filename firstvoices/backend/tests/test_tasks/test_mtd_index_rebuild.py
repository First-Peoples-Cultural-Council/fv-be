import pytest

from backend.models import Category, DictionaryEntry, Site
from backend.models.constants import AppRole, Visibility
from backend.models.media import Audio, Image
from backend.models.sites import SiteFeature
from backend.tests.factories import get_app_admin


@pytest.mark.django_db
class TestMtdIndexRebuild:
    # Test if the mtd index rebuild is triggered only when required
    # Mocking rebuild_mtd_index method from mtd_signals.py
    # To also test functionality of the associated signals, using models instead of test factories

    @pytest.fixture(scope="function", autouse=True)
    def mocked_mtd_index_func(self, mocker):
        self.mocked_func = mocker.patch(
            "backend.models.signals.mtd_signals.rebuild_mtd_index"
        )

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

    def test_public_entry_updated(self):
        entry = DictionaryEntry(
            title="test_entry", site=self.site, visibility=Visibility.PUBLIC
        )
        entry.save()

        assert self.mocked_func.call_count == 1
        self.mocked_func.assert_called_once_with(self.site.slug)

        entry.title = "Entry updated"
        entry.save()

        assert self.mocked_func.call_count == 2
        self.mocked_func.assert_called_with(self.site.slug)

        # Deleting entry
        entry.delete()
        assert self.mocked_func.call_count == 3
        self.mocked_func.assert_called_with(self.site.slug)

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    def test_non_public_entry_updated(self, visibility):
        entry = DictionaryEntry(site=self.site, visibility=visibility)
        entry.save()

        # mtd index rebuild should not be triggered
        assert self.mocked_func.call_count == 0

        entry.title = "Entry updated"
        entry.save()

        assert self.mocked_func.call_count == 0

        # Deleting entry
        entry.delete()
        assert self.mocked_func.call_count == 0

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    def test_non_public_to_public_visibility_change(self, visibility):
        entry = DictionaryEntry(site=self.site, visibility=visibility)
        entry.save()

        assert self.mocked_func.call_count == 0

        entry.visibility = Visibility.PUBLIC
        entry.save()

        assert self.mocked_func.call_count == 1
        self.mocked_func.assert_called_with(self.site.slug)

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    def test_public_to_non_public_visibility_change(self, visibility):
        entry = DictionaryEntry(site=self.site, visibility=Visibility.PUBLIC)
        entry.save()

        assert self.mocked_func.call_count == 1

        entry.visibility = visibility
        entry.save()

        assert self.mocked_func.call_count == 2
        self.mocked_func.assert_called_with(self.site.slug)

    def test_category_updated_public_entry(self):
        category = Category(
            title="test_category",
            site=self.site,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        category.save()
        entry = DictionaryEntry(
            site=self.site,
            visibility=Visibility.PUBLIC,
            translations=["Test Translation"],
        )
        entry.categories.add(category)

        entry.save()
        assert self.mocked_func.call_count == 1

        category.title = "Updated category title"
        category.save()
        assert self.mocked_func.call_count == 2
        self.mocked_func.assert_called_with(self.site.slug)

    def test_category_updated_public_entry_no_translation(self):
        category = Category(
            title="test_category",
            site=self.site,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        category.save()
        entry = DictionaryEntry(
            site=self.site, visibility=Visibility.PUBLIC, translations=[]
        )
        entry.categories.add(category)

        entry.save()
        assert self.mocked_func.call_count == 1

        category.title = "Updated category"
        category.save()

        # Should not trigger rebuild of index
        assert self.mocked_func.call_count == 1
        self.mocked_func.assert_called_with(self.site.slug)

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    def test_category_updated_non_public_entry(self, visibility):
        category = Category(
            title="test_category",
            site=self.site,
            created_by=self.admin_user,
            last_modified_by=self.admin_user,
        )
        category.save()
        entry = DictionaryEntry(site=self.site, visibility=visibility)
        entry.categories.add(category)

        entry.save()
        assert self.mocked_func.call_count == 0

        category.title = "Category title updated"
        category.save()

        # Should not trigger the rebuild of index
        assert self.mocked_func.call_count == 0

    def test_related_image_updated(self):
        image = Image(title="test image", site=self.site)
        image.save()

        entry = DictionaryEntry(site=self.site, visibility=Visibility.PUBLIC)
        entry.save()

        assert self.mocked_func.call_count == 1

        entry.related_images.add(image)
        entry.save()

        assert self.mocked_func.call_count == 2

        entry.related_images.remove(image)
        entry.save()

        assert self.mocked_func.call_count == 3
        self.mocked_func.assert_called_with(self.site.slug)

    def test_related_audio_updated(self):
        audio = Audio(title="test audio", site=self.site)
        audio.save()

        entry = DictionaryEntry(site=self.site, visibility=Visibility.PUBLIC)
        entry.save()

        assert self.mocked_func.call_count == 1

        entry.related_audio.add(audio)
        entry.save()

        assert self.mocked_func.call_count == 2

        entry.related_audio.remove(audio)
        entry.save()

        assert self.mocked_func.call_count == 3
        self.mocked_func.assert_called_with(self.site.slug)

    def test_mtd_rebuld_not_run_on_entry_if_indexing_paused(self):
        SiteFeature.objects.create(
            site=self.site, key="indexing_paused", is_enabled=True
        )

        entry = DictionaryEntry(
            title="test_entry", site=self.site, visibility=Visibility.PUBLIC
        )
        entry.save()

        assert self.mocked_func.call_count == 0
