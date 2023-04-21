import pytest
from backend.models.constants import AppRole, Role, Visibility
from backend.predicates import view_models
from backend.tests.factories import (
    MembershipFactory,
    SiteFactory,
    UserFactory,
    get_anonymous_user,
    get_app_admin,
    get_non_member_user,
    get_site_with_member,
)


class TestCanViewSiteModel:
    @pytest.mark.parametrize("get_user", [get_anonymous_user, get_non_member_user])
    @pytest.mark.parametrize("site_visibility", [Visibility.MEMBERS, Visibility.PUBLIC])
    @pytest.mark.django_db
    def test_non_members_see_non_team_site_models(self, site_visibility, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=site_visibility)
        assert view_models.can_view_site_model(user, site)

    @pytest.mark.parametrize("get_user", [get_anonymous_user, get_non_member_user])
    @pytest.mark.django_db
    def test_non_members_blocked_from_team_site_models(self, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=Visibility.TEAM)
        assert not view_models.can_view_site_model(user, site)

    @pytest.mark.parametrize("site_visibility", [Visibility.MEMBERS, Visibility.PUBLIC])
    @pytest.mark.django_db
    def test_members_see_non_team_site_models(self, site_visibility):
        (site, user) = get_site_with_member(site_visibility, Role.MEMBER)
        assert view_models.can_view_site_model(user, site)

    @pytest.mark.django_db
    def test_members_blocked_from_team_site_models(self):
        (site, user) = get_site_with_member(Visibility.TEAM, Role.MEMBER)
        assert not view_models.can_view_site_model(user, site)

    @pytest.mark.parametrize(
        "site_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.parametrize(
        "user_role", [Role.EDITOR, Role.ASSISTANT, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_team_always_see_own_site_models(self, site_visibility, user_role):
        (site, user) = get_site_with_member(site_visibility, user_role)
        assert view_models.can_view_site_model(user, site)

    @pytest.mark.parametrize("site_visibility", [Visibility.MEMBERS, Visibility.PUBLIC])
    @pytest.mark.parametrize(
        "user_role", [Role.EDITOR, Role.ASSISTANT, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_team_see_other_non_team_site_models(self, site_visibility, user_role):
        (site, user) = get_site_with_member(Visibility.PUBLIC, user_role)
        site2 = SiteFactory.create(visibility=site_visibility)
        assert view_models.can_view_site_model(user, site2)

    @pytest.mark.parametrize(
        "user_role", [Role.EDITOR, Role.ASSISTANT, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_team_blocked_from_other_team_site_models(self, user_role):
        (site, user) = get_site_with_member(Visibility.PUBLIC, user_role)
        site2 = SiteFactory.create(visibility=Visibility.TEAM)
        assert not view_models.can_view_site_model(user, site2)

    @pytest.mark.parametrize(
        "site_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.parametrize("role", [AppRole.STAFF, AppRole.SUPERADMIN])
    @pytest.mark.django_db
    def test_app_admins_always_see_site_models(self, site_visibility, role):
        user = get_app_admin(role)
        site = SiteFactory.build(visibility=site_visibility)

        assert view_models.can_view_site_model(user, site)


class TestCanViewMembershipModel:
    @pytest.mark.parametrize(
        "site_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.django_db
    def test_user_can_view_own_membership(self, site_visibility):
        user = UserFactory.create()
        site = SiteFactory.create(visibility=site_visibility)
        membership = MembershipFactory.create(site=site, user=user, role=Role.MEMBER)
        assert view_models.can_view_membership_model(user, membership)

    @pytest.mark.parametrize(
        "site_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    @pytest.mark.django_db
    def test_user_blocked_from_other_membership(self, site_visibility, role):
        user = UserFactory.create()
        user2 = UserFactory.create()
        site = SiteFactory.create(visibility=site_visibility)
        membership = MembershipFactory.create(site=site, user=user2, role=role)
        assert not view_models.can_view_membership_model(user, membership)

    @pytest.mark.parametrize(
        "site_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.django_db
    def test_language_admin_can_see_other_membership(self, site_visibility):
        user = UserFactory.create()
        user2 = UserFactory.create()
        site = SiteFactory.create(visibility=site_visibility)
        MembershipFactory.create(site=site, user=user, role=Role.LANGUAGE_ADMIN)
        membership2 = MembershipFactory.create(site=site, user=user2, role=Role.MEMBER)
        assert view_models.can_view_membership_model(user, membership2)

    @pytest.mark.parametrize(
        "site_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.django_db
    def test_language_admin_blocked_from_membership_on_other_site(
        self, site_visibility
    ):
        user = UserFactory.create()
        user2 = UserFactory.create()
        site = SiteFactory.create(visibility=site_visibility)
        site2 = SiteFactory.create(visibility=site_visibility)
        MembershipFactory.create(site=site, user=user, role=Role.LANGUAGE_ADMIN)
        membership2 = MembershipFactory.create(site=site2, user=user2, role=Role.MEMBER)
        assert not view_models.can_view_membership_model(user, membership2)

    @pytest.mark.parametrize("role", [AppRole.STAFF, AppRole.SUPERADMIN])
    @pytest.mark.parametrize(
        "site_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.django_db
    def test_app_admins_see_all_memberships(self, site_visibility, role):
        user = UserFactory.create()
        site = SiteFactory.create(visibility=site_visibility)
        membership = MembershipFactory.create(site=site, user=user, role=Role.MEMBER)

        admin_user = get_app_admin(role)

        assert view_models.can_view_membership_model(admin_user, membership)
