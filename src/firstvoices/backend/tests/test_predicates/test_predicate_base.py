import pytest

from firstvoices.backend.models.constants import AppRole, Role, Visibility
from firstvoices.backend.predicates import base
from firstvoices.backend.tests.factories import (
    AnonymousUserFactory,
    ControlledSiteContentFactory,
    MembershipFactory,
    SiteFactory,
    UncontrolledSiteContentFactory,
    UserFactory,
    get_app_admin,
)


class TestBaseObjectVisibilityPredicates:
    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    def test_is_public_obj_false(self, visibility):
        obj = ControlledSiteContentFactory.build(visibility=visibility)
        assert base.is_public_obj(None, obj) is False

    def test_is_public_obj_true(self):
        obj = ControlledSiteContentFactory.build(visibility=Visibility.PUBLIC)
        assert base.is_public_obj(None, obj)

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.PUBLIC])
    def test_is_members_obj_false(self, visibility):
        obj = ControlledSiteContentFactory.build(visibility=visibility)
        assert base.is_members_obj(None, obj) is False

    def test_is_members_obj_true(self):
        obj = ControlledSiteContentFactory.build(visibility=Visibility.MEMBERS)
        assert base.is_members_obj(None, obj)

    @pytest.mark.parametrize("visibility", [Visibility.MEMBERS, Visibility.PUBLIC])
    def test_is_team_obj_false(self, visibility):
        obj = ControlledSiteContentFactory.build(visibility=visibility)
        assert base.is_team_obj(None, obj) is False

    def test_is_team_obj_true(self):
        obj = ControlledSiteContentFactory.build(visibility=Visibility.TEAM)
        assert base.is_team_obj(None, obj)

    def test_is_own_object_true(self):
        user = UserFactory.build(id=1)
        obj = MembershipFactory.build(user=user)
        assert base.is_own_obj(user, obj)

    def test_is_own_object_false(self):
        user = UserFactory.build(id=1)
        user_two = UserFactory.build(id=2)
        obj = MembershipFactory.build(user=user)
        assert base.is_own_obj(user_two, obj) is False


class TestBaseSiteVisibilityPredicates:
    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.MEMBERS])
    def test_has_public_site_false(self, visibility):
        obj = ControlledSiteContentFactory.build(site__visibility=visibility)
        assert base.has_public_site(None, obj) is False

    def test_has_public_site_true(self):
        obj = ControlledSiteContentFactory.build(site__visibility=Visibility.PUBLIC)
        assert base.has_public_site(None, obj)

    @pytest.mark.parametrize("visibility", [Visibility.TEAM, Visibility.PUBLIC])
    def test_has_members_site_false(self, visibility):
        obj = ControlledSiteContentFactory.build(site__visibility=visibility)
        assert base.has_members_site(None, obj) is False

    def test_has_members_site_true(self):
        obj = ControlledSiteContentFactory.build(site__visibility=Visibility.MEMBERS)
        assert base.has_members_site(None, obj)

    @pytest.mark.parametrize("visibility", [Visibility.MEMBERS, Visibility.PUBLIC])
    def test_has_team_site_false(self, visibility):
        obj = ControlledSiteContentFactory.build(site__visibility=visibility)
        assert base.has_team_site(None, obj) is False

    def test_has_team_site_true(self):
        obj = ControlledSiteContentFactory.build(site__visibility=Visibility.TEAM)
        assert base.has_team_site(None, obj)


class TestBaseSiteRolePredicates:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    def test_is_at_least_member_true(self, role):
        user = UserFactory.create(id=1)
        site = SiteFactory.create(id=1)
        MembershipFactory.create(user=user, site=site)
        obj = ControlledSiteContentFactory.build(site=site)
        assert base.is_at_least_member(user, obj)

    @pytest.mark.django_db
    def test_is_at_least_member_false(self):
        user = UserFactory.create(id=1)
        site = SiteFactory.create(id=1)
        obj = ControlledSiteContentFactory.build(site=site)
        assert base.is_at_least_member(user, obj) is False

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    def test_is_at_least_assistant_true(self, role):
        user = UserFactory.create(id=1)
        site = SiteFactory.create(id=1)
        MembershipFactory.create(user=user, site=site, role=role)
        obj = ControlledSiteContentFactory.build(site=site)
        assert base.is_at_least_assistant(user, obj)

    @pytest.mark.django_db
    def test_is_at_least_assistant_false(self):
        user = UserFactory.create(id=1)
        site = SiteFactory.create(id=1)
        MembershipFactory.create(user=user, site=site, role=Role.MEMBER)
        obj = ControlledSiteContentFactory.build(site=site)
        assert base.is_at_least_assistant(user, obj) is False

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.EDITOR, Role.LANGUAGE_ADMIN])
    def test_is_at_least_editor_true(self, role):
        user = UserFactory.create(id=1)
        site = SiteFactory.create(id=1)
        MembershipFactory.create(user=user, site=site, role=role)
        obj = ControlledSiteContentFactory.build(site=site)
        assert base.is_at_least_editor(user, obj)

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT])
    def test_is_at_least_editor_false(self, role):
        user = UserFactory.create(id=1)
        site = SiteFactory.create(id=1)
        MembershipFactory.create(user=user, site=site, role=role)
        obj = ControlledSiteContentFactory.build(site=site)
        assert base.is_at_least_editor(user, obj) is False

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.LANGUAGE_ADMIN])
    def test_is_at_least_language_admin_true(self, role):
        user = UserFactory.create(id=1)
        site = SiteFactory.create(id=1)
        MembershipFactory.create(user=user, site=site, role=role)
        obj = ControlledSiteContentFactory.build(site=site)
        assert base.is_at_least_language_admin(user, obj)

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR])
    def test_is_at_least_language_admin_false(self, role):
        user = UserFactory.create(id=1)
        site = SiteFactory.create(id=1)
        MembershipFactory.create(user=user, site=site, role=role)
        obj = ControlledSiteContentFactory.build(site=site)
        assert base.is_at_least_language_admin(user, obj) is False

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "predicate",
        [
            base.is_at_least_member,
            base.is_at_least_assistant,
            base.is_at_least_editor,
            base.is_at_least_language_admin,
        ],
    )
    def test_is_anonymous(self, predicate):
        user = AnonymousUserFactory.build()
        site = SiteFactory.create(id=1)
        obj = ControlledSiteContentFactory.build(site=site)
        assert predicate(user, obj) is False

    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [AppRole.STAFF, AppRole.SUPERADMIN])
    def test_is_at_least_staff_admin_true(self, role):
        user = get_app_admin(role)
        assert base.is_at_least_staff_admin(user, None)

    @pytest.mark.django_db
    def test_is_at_least_staff_admin_false(self):
        user = UserFactory.create(id=1)
        assert not base.is_at_least_staff_admin(user, None)

    @pytest.mark.django_db
    def test_is_superadmin_true(self):
        user = get_app_admin(AppRole.SUPERADMIN)
        assert base.is_superadmin(user, None)

    @pytest.mark.django_db
    def test_is_superadmin_wrong_role(self):
        user = get_app_admin(AppRole.STAFF)
        assert not base.is_superadmin(user, None)

    @pytest.mark.django_db
    def test_is_superadmin_false(self):
        user = UserFactory.create(id=1)
        assert not base.is_superadmin(user, None)


class TestBaseAppRolePredicates:
    @pytest.mark.django_db
    @pytest.mark.parametrize("role", [AppRole.STAFF, AppRole.SUPERADMIN])
    def test_is_at_least_staff_true(self, role):
        user = get_app_admin(role)
        obj = SiteFactory.create(id=1)
        assert base.is_at_least_staff_admin(user, obj)

    @pytest.mark.django_db
    def test_is_at_least_staff_false(self):
        user = UserFactory.create()
        obj = SiteFactory.create()
        assert not base.is_at_least_staff_admin(user, obj)

    @pytest.mark.django_db
    def test_is_superadmin_true(self):
        user = get_app_admin(AppRole.SUPERADMIN)
        obj = SiteFactory.create()
        assert base.is_superadmin(user, obj)

    @pytest.mark.django_db
    def test_is_superadmin_wrong_role(self):
        user = get_app_admin(AppRole.STAFF)
        obj = SiteFactory.create(id=1)
        assert not base.is_superadmin(user, obj)

    @pytest.mark.django_db
    def test_is_superadmin_false(self):
        user = UserFactory.create()
        obj = SiteFactory.create()
        assert not base.is_superadmin(user, obj)


class TestBaseObjectAccessPredicates:
    @pytest.mark.parametrize("site_visibility", [Visibility.MEMBERS, Visibility.PUBLIC])
    @pytest.mark.parametrize("obj_visibility", [Visibility.MEMBERS, Visibility.PUBLIC])
    @pytest.mark.parametrize(
        "role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_has_member_access_true(self, site_visibility, obj_visibility, role):
        site = SiteFactory.create(visibility=site_visibility)
        obj = ControlledSiteContentFactory.create(site=site, visibility=obj_visibility)
        member_user = UserFactory.create()
        MembershipFactory(site=site, user=member_user, role=role)
        assert base.has_member_access_to_obj(member_user, obj)

    @pytest.mark.django_db
    def test_has_member_access_guest_user(self):
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(
            site=site, visibility=Visibility.MEMBERS
        )
        guest_user = AnonymousUserFactory.build()
        assert not base.has_member_access_to_obj(guest_user, obj)

    @pytest.mark.django_db
    def test_has_member_access_non_member(self):
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(
            site=site, visibility=Visibility.MEMBERS
        )
        non_member_user = UserFactory.create()
        assert not base.has_member_access_to_obj(non_member_user, obj)

    @pytest.mark.django_db
    def test_has_member_access_for_member_of_wrong_site(self):
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(
            site=site, visibility=Visibility.MEMBERS
        )
        other_member_user = UserFactory.create()
        site2 = SiteFactory.create()
        MembershipFactory.create(user=other_member_user, site=site2)
        assert not base.has_member_access_to_obj(other_member_user, obj)

    @pytest.mark.django_db
    def test_has_member_access_wrong_object_visibility(self):
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(site=site, visibility=Visibility.TEAM)
        member_user = UserFactory.create()
        MembershipFactory(site=site, user=member_user, role=Role.MEMBER)
        assert not base.has_member_access_to_obj(member_user, obj)

    @pytest.mark.django_db
    def test_has_member_access_wrong_site_visibility(self):
        site = SiteFactory.create(visibility=Visibility.TEAM)
        obj = ControlledSiteContentFactory.create(
            site=site, visibility=Visibility.MEMBERS
        )
        member_user = UserFactory.create()
        MembershipFactory(site=site, user=member_user, role=Role.MEMBER)
        assert not base.has_member_access_to_obj(member_user, obj)

    @pytest.mark.parametrize(
        "site_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.parametrize(
        "obj_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_has_team_access_true(self, site_visibility, obj_visibility, role):
        site = SiteFactory.create(visibility=site_visibility)
        obj = ControlledSiteContentFactory.create(site=site, visibility=obj_visibility)
        team_user = UserFactory.create()
        MembershipFactory(site=site, user=team_user, role=role)
        assert base.has_team_access_to_obj(team_user, obj)

    @pytest.mark.django_db
    def test_has_team_access_wrong_role(self):
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(site=site, visibility=Visibility.TEAM)
        member_user = UserFactory.create()
        MembershipFactory(site=site, user=member_user, role=Role.MEMBER)
        assert not base.has_team_access_to_obj(member_user, obj)

    @pytest.mark.django_db
    def test_has_team_access_guest_user(self):
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(site=site, visibility=Visibility.TEAM)
        guest_user = AnonymousUserFactory.build()
        assert not base.has_team_access_to_obj(guest_user, obj)

    @pytest.mark.django_db
    def test_has_team_access_non_member(self):
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(site=site, visibility=Visibility.TEAM)
        non_member_user = UserFactory.create()
        assert not base.has_team_access_to_obj(non_member_user, obj)

    @pytest.mark.django_db
    def test_team_is_blocked_from_team_content_on_other_sites(self):
        site1 = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(
            site=site1, visibility=Visibility.TEAM
        )
        other_member_user = UserFactory.create()
        site2 = SiteFactory.create()
        MembershipFactory.create(
            user=other_member_user, site=site2, role=Role.LANGUAGE_ADMIN
        )
        MembershipFactory.create(user=other_member_user, site=site1, role=Role.MEMBER)
        assert not base.has_member_access_to_obj(other_member_user, obj)


class TestBaseSiteAccessPredicates:
    @pytest.mark.parametrize(
        "role", [Role.MEMBER, Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN]
    )
    @pytest.mark.django_db
    def test_has_member_access_true(self, role):
        site = SiteFactory.create(visibility=Visibility.MEMBERS)
        obj = UncontrolledSiteContentFactory.create(site=site)
        member_user = UserFactory.create()
        MembershipFactory(site=site, user=member_user, role=role)
        assert base.has_member_access_to_site(member_user, obj)

    @pytest.mark.django_db
    def test_has_member_access_guest_user(self):
        site = SiteFactory.create(visibility=Visibility.MEMBERS)
        obj = UncontrolledSiteContentFactory.create(site=site)
        guest_user = AnonymousUserFactory.build()
        assert not base.has_member_access_to_site(guest_user, obj)

    @pytest.mark.django_db
    def test_has_member_access_non_member(self):
        site = SiteFactory.create(visibility=Visibility.MEMBERS)
        obj = UncontrolledSiteContentFactory.create(site=site)
        non_member_user = UserFactory.create()
        assert not base.has_member_access_to_site(non_member_user, obj)

    @pytest.mark.django_db
    def test_has_member_access_wrong_site_visibility(self):
        site = SiteFactory.create(visibility=Visibility.TEAM)
        obj = UncontrolledSiteContentFactory.create(site=site)
        member_user = UserFactory.create()
        MembershipFactory(site=site, user=member_user, role=Role.MEMBER)
        assert not base.has_member_access_to_site(member_user, obj)

    @pytest.mark.django_db
    def test_has_member_access_different_site(self):
        site1 = SiteFactory.create(visibility=Visibility.MEMBERS)
        obj = UncontrolledSiteContentFactory.create(site=site1)
        other_member_user = UserFactory.create()
        site2 = SiteFactory.create()
        MembershipFactory.create(
            user=other_member_user, site=site2, role=Role.LANGUAGE_ADMIN
        )
        assert not base.has_member_access_to_site(other_member_user, obj)

    @pytest.mark.parametrize(
        "site_visibility", [Visibility.TEAM, Visibility.MEMBERS, Visibility.PUBLIC]
    )
    @pytest.mark.parametrize("role", [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_has_team_access_true(self, site_visibility, role):
        site = SiteFactory.create(visibility=site_visibility)
        obj = UncontrolledSiteContentFactory.create(site=site)
        team_user = UserFactory.create()
        MembershipFactory(site=site, user=team_user, role=role)
        assert base.has_team_access_to_site(team_user, obj)

    @pytest.mark.django_db
    def test_has_team_access_wrong_role(self):
        site = SiteFactory.create(visibility=Visibility.TEAM)
        obj = UncontrolledSiteContentFactory.create(site=site)
        member_user = UserFactory.create()
        MembershipFactory(site=site, user=member_user, role=Role.MEMBER)
        assert not base.has_team_access_to_site(member_user, obj)

    @pytest.mark.django_db
    def test_has_team_access_guest_user(self):
        site = SiteFactory.create(visibility=Visibility.TEAM)
        obj = UncontrolledSiteContentFactory.create(site=site)
        guest_user = AnonymousUserFactory.build()
        assert not base.has_team_access_to_site(guest_user, obj)

    @pytest.mark.django_db
    def test_has_team_access_non_member(self):
        site = SiteFactory.create(visibility=Visibility.TEAM)
        obj = UncontrolledSiteContentFactory.create(site=site)
        non_member_user = UserFactory.create()
        assert not base.has_team_access_to_site(non_member_user, obj)

    @pytest.mark.django_db
    def test_team_has_member_access_on_different_site(self):
        site1 = SiteFactory.create(visibility=Visibility.TEAM)
        obj = UncontrolledSiteContentFactory.create(site=site1)
        other_member_user = UserFactory.create()
        site2 = SiteFactory.create()
        MembershipFactory.create(
            user=other_member_user, site=site2, role=Role.LANGUAGE_ADMIN
        )
        MembershipFactory.create(user=other_member_user, site=site1, role=Role.MEMBER)
        assert not base.has_member_access_to_site(other_member_user, obj)
