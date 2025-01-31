import pytest
from django.core.management import call_command

from backend.models.constants import AppRole
from backend.models.sites import Site, SiteFeature, SiteMenu
from backend.tests.factories import (
    SiteFactory,
    SiteFeatureFactory,
    SiteMenuFactory,
    get_app_admin,
)


@pytest.mark.django_db
class TestCopySite:
    SOURCE_SLUG = "old"
    TARGET_SLUG = "new"

    def setup_method(self):
        self.old_site = SiteFactory.create(slug=self.SOURCE_SLUG)
        self.user = get_app_admin(AppRole.SUPERADMIN)

    def call_default_command(self):
        # helper function
        call_command(
            "copy_site",
            source_slug=self.SOURCE_SLUG,
            target_slug=self.TARGET_SLUG,
            email=self.user.email,
        )

    def test_source_site_exists(self):
        with pytest.raises(AttributeError) as e:
            call_command(
                "copy_site",
                source_slug="does_not_exist",
                target_slug=self.TARGET_SLUG,
                email=self.EMAIL,
            )
        assert str(e.value) == "Provided source site does not exist."

    def test_target_site_does_not_exist(self):
        SiteFactory.create(slug=self.TARGET_SLUG)
        with pytest.raises(AttributeError) as e:
            self.call_default_command()
        assert (
            str(e.value)
            == f"Site with slug {self.TARGET_SLUG} already exists. Please use a different target slug."
        )

    def test_target_user_does_not_exist(self):
        with pytest.raises(AttributeError) as e:
            self.call_default_command()
        assert str(e.value) == "No user found with the provided email."

    def test_new_site_attributes(self):
        self.call_default_command()

        old_site = Site.objects.get(slug=self.SOURCE_SLUG)
        new_site = Site.objects.get(slug=self.TARGET_SLUG)

        assert new_site.title == self.TARGET_SLUG
        assert new_site.language == old_site.language
        assert new_site.visibility == old_site.visibility
        assert new_site.is_hidden == old_site.is_hidden

        assert new_site.created_by.email == self.user.email
        assert new_site.last_modified_by.email == self.user.email

    def test_site_features(self):
        sf_1 = SiteFeatureFactory.create(
            site=self.old_site, key="first_feature", is_enabled=True
        )
        sf_2 = SiteFeatureFactory.create(
            site=self.old_site, key="second_feature", is_enabled=False
        )

        self.call_default_command()

        sf_1_new = SiteFeature.objects.get(
            site__slug=self.TARGET_SLUG, key="first_feature"
        )
        sf_2_new = SiteFeature.objects.get(
            site__slug=self.TARGET_SLUG, key="second_feature"
        )

        assert sf_1_new.is_enabled == sf_1.is_enabled
        assert sf_2_new.is_enabled == sf_2.is_enabled

    def test_site_menu(self):
        old_site_menu = SiteMenuFactory.create(site=self.old_site)

        self.call_default_command()

        new_site_menu = SiteMenu.objects.get(site__slug=self.TARGET_SLUG)

        assert new_site_menu.json == old_site_menu.json
