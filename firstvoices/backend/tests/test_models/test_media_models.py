import pytest

from backend.tests import factories


class TestMediaModels:
    media_factories = [
        factories.ImageFactory,
        factories.AudioFactory,
        factories.VideoFactory,
    ]

    @pytest.mark.parametrize("media_factory", media_factories)
    @pytest.mark.django_db
    def test_upload_folder(self, media_factory):
        site = factories.SiteFactory.create()
        media_instance = media_factory.create(site=site)
        media_file = media_instance.content
        assert media_file.file
        assert f"/{site.slug}/" in media_file.path

    @pytest.mark.parametrize("media_factory", media_factories)
    @pytest.mark.django_db
    def test_file_deleted(self, media_factory):
        media_instance = media_factory.create()
        media_file = media_instance.content
        assert media_file.file

        media_instance.delete()

        try:
            media_file.file
            assert False
        except ValueError:
            assert True
