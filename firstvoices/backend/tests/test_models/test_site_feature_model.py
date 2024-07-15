import pytest

from backend.models.sites import SiteFeature
from backend.tests.factories import SiteFactory


class TestSiteFeatureModel:
    """
    Tests for the SiteFeature model.
    Primarily tests that the model does not trigger a media sync outside of the API.
    """

    @pytest.fixture(scope="function", autouse=True)
    def mocked_media_async_func(self, mocker):
        self.mocked_func = mocker.patch(
            "backend.search.tasks.site_content_indexing_tasks.sync_all_media_site_content_in_indexes.apply_async"
        )

    @pytest.fixture
    def site(self):
        return SiteFactory.create(slug="test")

    @pytest.mark.django_db
    def test_create_does_not_trigger_media_sync(self, site):
        SiteFeature.objects.create(site=site, key="test_key", is_enabled=True)
        assert self.mocked_func.call_count == 0

    @pytest.mark.django_db
    def test_update_does_not_trigger_media_sync(self, site):
        feature = SiteFeature.objects.create(site=site, key="test_key", is_enabled=True)
        feature.is_enabled = False
        feature.save()
        assert self.mocked_func.call_count == 0

    @pytest.mark.django_db
    def test_delete_does_not_trigger_media_sync(self, site):
        feature = SiteFeature.objects.create(site=site, key="test_key", is_enabled=True)
        feature.delete()
        assert self.mocked_func.call_count == 0
