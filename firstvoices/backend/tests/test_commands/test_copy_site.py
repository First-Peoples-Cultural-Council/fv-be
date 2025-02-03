import pytest
from django.core.management import call_command

from backend.models.category import Category
from backend.models.characters import (
    Alphabet,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from backend.models.constants import AppRole
from backend.models.sites import Site, SiteFeature, SiteMenu
from backend.tests.factories import (
    AlphabetFactory,
    CharacterFactory,
    CharacterVariantFactory,
    ChildCategoryFactory,
    IgnoredCharacterFactory,
    ParentCategoryFactory,
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
                email=self.user.email,
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
            call_command(
                "copy_site",
                source_slug=self.SOURCE_SLUG,
                target_slug=self.TARGET_SLUG,
                email="notareal@email.com",
            )
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

    def test_characters_and_variants(self):
        old_char = CharacterFactory(site=self.old_site)
        old_char_variant = CharacterVariantFactory(
            site=self.old_site, base_character=old_char
        )

        self.call_default_command()

        new_char = Character.objects.get(site__slug=self.TARGET_SLUG)
        new_char_variant = CharacterVariant.objects.get(site__slug=self.TARGET_SLUG)

        assert new_char.title == old_char.title
        assert new_char.sort_order == old_char.sort_order
        assert new_char_variant.title == old_char_variant.title
        assert new_char_variant.base_character == new_char

    def test_ignored_characters(self):
        old_char = IgnoredCharacterFactory(site=self.old_site)

        self.call_default_command()

        new_char = IgnoredCharacter.objects.get(site__slug=self.TARGET_SLUG)

        assert new_char.title == old_char.title

    def test_alphabet(self):
        old_alphabet = AlphabetFactory(
            site=self.old_site, input_to_canonical_map="[{'in': '2', 'out': 'two'}]"
        )

        self.call_default_command()

        new_alphabet = Alphabet.objects.get(site__slug=self.TARGET_SLUG)

        assert (
            new_alphabet.input_to_canonical_map == old_alphabet.input_to_canonical_map
        )

    def test_category(self):
        # Removing default categories from old site
        Category.objects.filter(site=self.old_site).delete()

        # Adding new categories
        old_parent_category = ParentCategoryFactory(site=self.old_site)
        old_child_category_1 = ChildCategoryFactory(
            site=self.old_site, parent=old_parent_category
        )
        old_child_category_2 = ChildCategoryFactory(
            site=self.old_site, parent=old_parent_category
        )

        old_extra_category = ParentCategoryFactory(site=self.old_site)

        self.call_default_command()

        assert Category.objects.filter(site__slug=self.TARGET_SLUG).count() == 4

        # parent category
        new_parent_category = Category.objects.filter(
            site__slug=self.TARGET_SLUG, children__isnull=False
        ).distinct()[0]
        assert new_parent_category.title == old_parent_category.title
        child_categories = new_parent_category.children.all()

        assert child_categories.count() == 2
        assert child_categories[0].title == old_child_category_1.title
        assert child_categories[1].title == old_child_category_2.title

        assert Category.objects.filter(
            site__slug=self.TARGET_SLUG, title=old_extra_category.title
        ).exists()
