import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from factory.django import DjangoModelFactory

from backend.models import JoinRequest
from backend.models.app import AppMembership
from backend.models.sites import Language, LanguageFamily, Membership, Site


class AnonymousUserFactory(DjangoModelFactory):
    """
    Note: use the build() strategy only with this factory, because these do not have a db table
    """

    class Meta:
        model = AnonymousUser


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: "user%03d@email.com" % n)


class LanguageFamilyFactory(DjangoModelFactory):
    class Meta:
        model = LanguageFamily

    title = factory.Sequence(lambda n: "Language Family %03d" % n)


class LanguageFactory(DjangoModelFactory):
    class Meta:
        model = Language

    title = factory.Sequence(lambda n: "Language %03d" % n)
    language_family = factory.SubFactory(LanguageFamilyFactory)


class SiteFactory(DjangoModelFactory):
    class Meta:
        model = Site

    title = factory.Sequence(lambda n: "Site %03d" % n)
    slug = factory.Sequence(lambda n: "site-%03d" % n)
    language = factory.SubFactory(LanguageFactory)

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


class JoinRequestFactory(DjangoModelFactory):
    class Meta:
        model = JoinRequest

    user = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)


def get_anonymous_user():
    return AnonymousUserFactory.build()


def get_non_member_user():
    return UserFactory.create()


def get_site_with_member(site_visibility, user_role, user=None):
    if user is None:
        user = UserFactory.create()
    site = SiteFactory.create(visibility=site_visibility)
    MembershipFactory.create(site=site, user=user, role=user_role)
    return site, user


def get_app_admin(role):
    user = UserFactory.create()
    AppMembershipFactory.create(user=user, role=role)
    return user
