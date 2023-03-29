import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from factory.django import DjangoModelFactory

from firstvoices.backend.models.app import AppMembership
from firstvoices.backend.models.dictionary import DictionaryEntry
from firstvoices.backend.models.sites import Membership, Site, SiteFeature


class SiteFactory(DjangoModelFactory):
    class Meta:
        model = Site

    title = factory.Sequence(lambda n: "Site %03d" % n)
    slug = factory.Sequence(lambda n: "site-%03d" % n)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: "username %03d" % n)
    id = factory.Sequence(lambda n: "user id %03d" % n)


class AnonymousUserFactory(DjangoModelFactory):
    """
    Note: use the build() strategy only with this factory, because these do not have a db table
    """

    class Meta:
        model = AnonymousUser


class MembershipFactory(DjangoModelFactory):
    class Meta:
        model = Membership

    user = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)


class AppMembershipFactory(DjangoModelFactory):
    class Meta:
        model = AppMembership

    user = factory.SubFactory(UserFactory)


class UncontrolledSiteContentFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        # use any concrete model that inherits from BaseSiteContentModel
        model = SiteFeature

    key = factory.Sequence(lambda n: "Uncontrolled content %03d" % n)


class ControlledSiteContentFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        # use any concrete model that inherits from BaseControlledSiteContentModel
        model = DictionaryEntry

    title = factory.Sequence(lambda n: "Controlled content %03d" % n)


def get_anonymous_user():
    return AnonymousUserFactory.build()


def get_non_member_user():
    return UserFactory.create()


def get_site_with_member(site_visibility, user_role):
    user = UserFactory.create()
    site = SiteFactory.create(visibility=site_visibility)
    MembershipFactory.create(site=site, user=user, role=user_role)
    return site, user
