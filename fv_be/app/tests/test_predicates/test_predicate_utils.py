import pytest

from fv_be.app.models.constants import Role
from fv_be.app.predicates import utils
from fv_be.app.tests.factories import (
    AnonymousUserFactory,
    ControlledSiteContentFactory,
    MembershipFactory,
    SiteFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestPredicateUtils:
    def test_get_site_id_for_site(self):
        site = SiteFactory.create()
        assert utils.get_site_id(site) == site.id

    def test_get_site_id_for_obj(self):
        site = SiteFactory.create()
        obj = ControlledSiteContentFactory.create(site=site)
        assert utils.get_site_id(obj) == site.id

    def test_get_role_for_guest(self):
        site = SiteFactory.create()
        obj = ControlledSiteContentFactory.create(site=site)
        guest_user = AnonymousUserFactory.build()
        assert utils.get_role(guest_user, obj) == -1

    def test_get_role_for_non_member(self):
        site = SiteFactory.create()
        obj = ControlledSiteContentFactory.create(site=site)
        lone_user = UserFactory.create()
        assert utils.get_role(lone_user, obj) == -1

    def test_get_role_for_member(self):
        site = SiteFactory.create()
        obj = ControlledSiteContentFactory.create(site=site)
        member_user = UserFactory.create()
        MembershipFactory(site=site, user=member_user, role=Role.MEMBER)
        assert utils.get_role(member_user, obj) == Role.MEMBER
