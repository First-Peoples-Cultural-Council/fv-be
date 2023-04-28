import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from factory.django import DjangoModelFactory

from backend.models.app import AppJson, AppMembership
from backend.models.category import Category
from backend.models.characters import (
    Alphabet,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from backend.models.dictionary import DictionaryEntry, DictionaryEntryLink
from backend.models.sites import (
    Language,
    LanguageFamily,
    Membership,
    Site,
    SiteFeature,
    SiteMenu,
)


class AnonymousUserFactory(DjangoModelFactory):
    """
    Note: use the build() strategy only with this factory, because these do not have a db table
    """

    class Meta:
        model = AnonymousUser


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    id = factory.Sequence(lambda n: "user id %03d" % n)
    email = factory.Sequence(lambda n: "user%03d@email.com" % n)


class SiteFactory(DjangoModelFactory):
    class Meta:
        model = Site

    title = factory.Sequence(lambda n: "Site %03d" % n)
    slug = factory.Sequence(lambda n: "site-%03d" % n)

    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)


class MembershipFactory(DjangoModelFactory):
    class Meta:
        model = Membership

    user = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)


class AppMembershipFactory(DjangoModelFactory):
    class Meta:
        model = AppMembership

    user = factory.SubFactory(UserFactory)


class SiteFeatureFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = SiteFeature

    key = factory.Sequence(lambda n: "Uncontrolled content %03d" % n)


class UncontrolledSiteContentFactory(SiteFeatureFactory):
    # use any concrete model that inherits from BaseSiteContentModel
    pass


class DictionaryEntryFactory(DjangoModelFactory):
    class Meta:
        model = DictionaryEntry

    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Dictionary entry %03d" % n)
    custom_order = factory.Sequence(lambda n: "sort order %03d" % n)


class ControlledSiteContentFactory(DictionaryEntryFactory):
    # use any concrete model that inherits from BaseControlledSiteContentModel
    pass


class DictionaryEntryLinkFactory(DjangoModelFactory):
    class Meta:
        model = DictionaryEntryLink

    from_dictionary_entry = factory.SubFactory(DictionaryEntryFactory)
    to_dictionary_entry = factory.SubFactory(DictionaryEntryFactory)


class LanguageFamilyFactory(DjangoModelFactory):
    class Meta:
        model = LanguageFamily

    title = factory.Sequence(lambda n: "Language Family %03d" % n)


class LanguageFactory(DjangoModelFactory):
    class Meta:
        model = Language

    title = factory.Sequence(lambda n: "Language %03d" % n)
    language_family = factory.SubFactory(LanguageFamilyFactory)


class SiteMenuFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = SiteMenu


class AppJsonFactory(DjangoModelFactory):
    class Meta:
        model = AppJson


class CharacterFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Character

    title = factory.Sequence(lambda n: "chr" + chr(n + 64))  # begin with A
    sort_order = factory.Sequence(int)


class CharacterVariantFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = CharacterVariant

    base_character = factory.SubFactory(CharacterFactory)
    title = factory.Sequence(lambda n: "varchr" + chr(n + 64))  # begin with A


class IgnoredCharacterFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = IgnoredCharacter

    title = factory.Sequence(lambda n: "%03d" % n)


class AlphabetFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Alphabet


class ParentCategoryFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)
    site = factory.SubFactory(SiteFactory)
    title = factory.Sequence(lambda n: "Category title %03d" % n)
    description = factory.Sequence(lambda n: "Category description %03d" % n)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)

    class Meta:
        model = Category


class ChildCategoryFactory(ParentCategoryFactory):
    parent = factory.SubFactory(ParentCategoryFactory)

    class Meta:
        model = Category


def get_anonymous_user():
    return AnonymousUserFactory.build()


def get_non_member_user():
    return UserFactory.create()


def get_site_with_member(site_visibility, user_role):
    user = UserFactory.create()
    site = SiteFactory.create(visibility=site_visibility)
    MembershipFactory.create(site=site, user=user, role=user_role)
    return site, user


def get_app_admin(role):
    user = UserFactory.create()
    AppMembershipFactory.create(user=user, role=role)
    return user
