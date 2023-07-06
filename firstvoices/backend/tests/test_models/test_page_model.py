import pytest
from django.db import IntegrityError

from backend.tests import factories


class TestSitePageModel:
    @pytest.mark.django_db
    def test_one_or_zero_banner(self):
        image = factories.ImageFactory.create()
        video = factories.VideoFactory.create()

        try:
            factories.SitePageFactory.create()
            factories.SitePageFactory.create(banner_image=image)
            factories.SitePageFactory.create(banner_video=video)
        except IntegrityError:
            pytest.fail("Failed when trying to add a banner to a page.")

        with pytest.raises(IntegrityError):
            factories.SitePageFactory.create(banner_image=image, banner_video=video)
            pytest.fail(
                "Expected error due to the page having a banner image and banner video."
            )
