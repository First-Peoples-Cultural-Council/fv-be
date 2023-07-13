import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from backend.models import validators
from backend.tests import factories


class TestSitePageModel:
    @pytest.mark.django_db
    def test_one_or_zero_banner(self):
        page = factories.SitePageFactory.create()
        image = factories.ImageFactory.create()
        video = factories.VideoFactory.create()

        # Check that a page cannot have both an image banner and a video banner at the same time
        with pytest.raises(IntegrityError):
            page.banner_image = image
            page.banner_video = video
            page.save()
            pytest.fail(
                "Expected error due to the page having a banner image and banner video at the same time."
            )

    @pytest.mark.django_db
    def test_same_slug_across_sites_allowed(self):
        site_one = factories.SiteFactory.create()
        site_two = factories.SiteFactory.create()

        try:
            factories.SitePageFactory.create(site=site_one, slug="slug-one")
            factories.SitePageFactory.create(site=site_two, slug="slug-one")
        except IntegrityError:
            pytest.fail(
                "Error when trying to create two pages on separate sites with the same slug."
            )

    @pytest.mark.django_db
    def test_same_slug_same_site_not_allowed(self):
        site = factories.SiteFactory.create()

        with pytest.raises(IntegrityError):
            factories.SitePageFactory.create(site=site, slug="slug-one")
            factories.SitePageFactory.create(site=site, slug="slug-one")
            pytest.fail(
                "Expected error when trying to create two pages on the same site with the same slug."
            )

    @pytest.mark.parametrize(
        "invalid_string",
        validators.RESERVED_SITE_PAGE_SLUG_LIST,
    )
    @pytest.mark.django_db
    def test_restricted_slug_validator(self, invalid_string):
        with pytest.raises(ValidationError):
            user = factories.UserFactory.create()
            page = factories.SitePageFactory.create(
                slug=f"test-{invalid_string}-invalid",
                created=timezone.now(),
                last_modified=timezone.now(),
                created_by=user,
                last_modified_by=user,
            )
            page.clean_fields()
            pytest.fail(
                "Expected error when trying to create site page with invalid string in slug."
            )
