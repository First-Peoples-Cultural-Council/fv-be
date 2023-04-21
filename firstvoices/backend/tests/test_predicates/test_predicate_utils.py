import pytest
from backend.models.constants import AppRole, Role
from backend.predicates import utils
from backend.tests.factories import (
    AnonymousUserFactory,
    ControlledSiteContentFactory,
    MembershipFactory,
    SiteFactory,
    UserFactory,
    get_app_admin,
)
from django.core.management import call_command


@pytest.mark.django_db
class TestPredicateUtils:
    # The default g2p config is required for tests that use DictionaryEntry, as an Alphabet is created for custom sort.
    @pytest.fixture
    def g2p_db_setup(self, django_db_blocker):
        with django_db_blocker.unblock():
            call_command("loaddata", "default_g2p_config.json")

    def test_get_site_id_for_site(self):
        site = SiteFactory.create()
        assert utils.get_site_id(site) == site.id

    def test_get_site_id_for_obj(self, g2p_db_setup):
        site = SiteFactory.create()
        obj = ControlledSiteContentFactory.create(site=site)
        assert utils.get_site_id(obj) == site.id

    def test_get_site_role_for_guest(self, g2p_db_setup):
        site = SiteFactory.create()
        obj = ControlledSiteContentFactory.create(site=site)
        guest_user = AnonymousUserFactory.build()
        assert utils.get_site_role(guest_user, obj) == -1

    def test_get_site_role_for_non_member(self, g2p_db_setup):
        site = SiteFactory.create()
        obj = ControlledSiteContentFactory.create(site=site)
        lone_user = UserFactory.create()
        assert utils.get_site_role(lone_user, obj) == -1

    def test_get_site_role_for_member(self, g2p_db_setup):
        site = SiteFactory.create()
        obj = ControlledSiteContentFactory.create(site=site)
        member_user = UserFactory.create()
        MembershipFactory(site=site, user=member_user, role=Role.MEMBER)
        assert utils.get_site_role(member_user, obj) == Role.MEMBER

    def test_get_app_role_for_guest(self):
        guest_user = AnonymousUserFactory.build()
        assert utils.get_app_role(guest_user) == -1

    def test_get_app_role_for_non_member(self):
        lone_user = UserFactory.create()
        assert utils.get_app_role(lone_user) == -1

    def test_get_app_role_for_member(self):
        member_user = get_app_admin(AppRole.STAFF)
        assert utils.get_app_role(member_user) == AppRole.STAFF
