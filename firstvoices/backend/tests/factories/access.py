import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from factory.django import DjangoModelFactory

from backend.models.app import AppMembership
from backend.models.constants import AppRole, Role, Visibility
from backend.models.sites import Language, LanguageFamily, Site
from backend.tests import factories


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
    first_name = factory.Sequence(lambda n: "Firsty%03d" % n)
    last_name = factory.Sequence(lambda n: "Lasty the %03d" % n)


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
    visibility = Visibility.PUBLIC

    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    system_last_modified_by = factory.SubFactory(UserFactory)


class AppMembershipFactory(DjangoModelFactory):
    class Meta:
        model = AppMembership

    user = factory.SubFactory(UserFactory)


def get_anonymous_user():
    return AnonymousUserFactory.build()


def get_non_member_user():
    return UserFactory.create()


def get_site_with_member(site_visibility, user_role, user=None):
    if user is None:
        user = UserFactory.create()
    site = SiteFactory.create(visibility=site_visibility)
    factories.MembershipFactory.create(site=site, user=user, role=user_role)
    return site, user


def get_app_admin(role):
    user = UserFactory.create()
    AppMembershipFactory.create(user=user, role=role)
    return user


def get_superadmin():
    return get_app_admin(AppRole.SUPERADMIN)


def get_member_of_other_site():
    _, user = get_site_with_member(Visibility.PUBLIC, Role.LANGUAGE_ADMIN)
    return user


def get_site_with_authenticated_member(
    client, visibility=Visibility.PUBLIC, role=Role.MEMBER
):
    site, user = factories.get_site_with_member(visibility, role)
    client.force_authenticate(user=user)
    return site, user


def get_site_with_authenticated_nonmember(client, visibility=Visibility.PUBLIC):
    site = factories.SiteFactory.create(visibility=visibility)
    user = factories.get_non_member_user()
    client.force_authenticate(user=user)
    return site, user


def get_site_with_staff_user(client=None, visibility=Visibility.PUBLIC):
    site = factories.SiteFactory.create(visibility=visibility)
    user = factories.get_app_admin(AppRole.STAFF)
    client.force_authenticate(user=user)
    return site, user


def get_site_with_anonymous_user(client=None, visibility=Visibility.PUBLIC):
    # client is intentionally ignored so all these site_with_user functions can have the same signature
    site = factories.SiteFactory.create(visibility=visibility)
    user = factories.get_anonymous_user()
    return site, user


def get_site_with_app_admin(
    client=None, visibility=Visibility.PUBLIC, role=AppRole.SUPERADMIN
):
    user = factories.get_app_admin(role)
    client.force_authenticate(user=user)
    site = factories.SiteFactory.create(visibility=visibility)
    return site, user
