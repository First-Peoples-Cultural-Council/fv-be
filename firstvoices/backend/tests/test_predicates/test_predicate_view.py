import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.predicates import view
from backend.tests.factories import (
    ControlledSiteContentFactory,
    MembershipFactory,
    SiteFactory,
    UncontrolledSiteContentFactory,
    UserFactory,
    get_anonymous_user,
    get_app_admin,
    get_non_member_user,
    get_site_with_member,
)


class TestIsVisibleObject:
    @pytest.mark.parametrize("get_user", [get_anonymous_user, get_non_member_user])
    @pytest.mark.django_db
    def test_non_members_see_public_content(self, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.build(
            site=site, visibility=Visibility.PUBLIC
        )
        assert view.is_visible_object(user, obj)

    @pytest.mark.parametrize(
        "visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize("get_user", [get_anonymous_user, get_non_member_user])
    @pytest.mark.django_db
    def test_non_members_blocked_for_private_sites(self, visibility, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=visibility)
        obj = ControlledSiteContentFactory.build(
            site=site, visibility=Visibility.PUBLIC
        )
        assert view.is_visible_object(user, obj) is False

    @pytest.mark.parametrize(
        "visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize("get_user", [get_anonymous_user, get_non_member_user])
    @pytest.mark.django_db
    def test_non_members_blocked_for_private_objects(self, visibility, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=visibility.PUBLIC)
        obj = ControlledSiteContentFactory.build(site=site, visibility=visibility)
        assert view.is_visible_object(user, obj) is False

    # members can see enabled + public (on own site)
    @pytest.mark.parametrize(
        "site_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS],
    )
    @pytest.mark.parametrize(
        "obj_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS],
    )
    @pytest.mark.django_db
    def test_members_see_members_content(self, site_visibility, obj_visibility):
        (site, user) = get_site_with_member(site_visibility, Role.MEMBER)
        obj = ControlledSiteContentFactory.build(site=site, visibility=obj_visibility)
        assert view.is_visible_object(user, obj)

    @pytest.mark.django_db
    def test_members_blocked_for_team_sites(self):
        (site, user) = get_site_with_member(Visibility.TEAM, Role.MEMBER)
        obj = ControlledSiteContentFactory.build(
            site=site, visibility=Visibility.PUBLIC
        )
        assert view.is_visible_object(user, obj) is False

    @pytest.mark.django_db
    def test_members_blocked_for_team_objects(self):
        (site, user) = get_site_with_member(Visibility.PUBLIC, Role.MEMBER)
        obj = ControlledSiteContentFactory.build(site=site, visibility=Visibility.TEAM)
        assert view.is_visible_object(user, obj) is False

    # team can see team + enabled + public (on own site)

    @pytest.mark.parametrize(
        "site_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "obj_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "role",
        [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.django_db
    def test_team_see_all_for_own_site(self, site_visibility, obj_visibility, role):
        (site, user) = get_site_with_member(site_visibility, role)
        obj = ControlledSiteContentFactory.build(site=site, visibility=obj_visibility)
        assert view.is_visible_object(user, obj)

    @pytest.mark.parametrize(
        "role",
        [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.django_db
    def test_team_see_public_content_for_other_sites(self, role):
        (site, user) = get_site_with_member(Visibility.TEAM, role)

        site2 = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.build(
            site=site2, visibility=Visibility.PUBLIC
        )
        assert view.is_visible_object(user, obj)

    @pytest.mark.parametrize(
        "obj_visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "role",
        [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.django_db
    def test_team_blocked_for_private_content_on_other_public_sites(
        self, obj_visibility, role
    ):
        user = UserFactory.create()
        site = SiteFactory.create()
        MembershipFactory.create(user=user, site=site, role=role)

        site2 = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.build(site=site2, visibility=obj_visibility)
        assert not view.is_visible_object(user, obj)

    @pytest.mark.parametrize(
        "site_visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "obj_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "role",
        [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.django_db
    def test_team_blocked_for_all_content_on_other_private_sites(
        self, site_visibility, obj_visibility, role
    ):
        user = UserFactory.create()
        site = SiteFactory.create()
        MembershipFactory.create(user=user, site=site, role=role)

        site2 = SiteFactory.create(visibility=site_visibility)
        obj = ControlledSiteContentFactory.build(site=site2, visibility=obj_visibility)
        assert not view.is_visible_object(user, obj)

    @pytest.mark.parametrize(
        "site_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "obj_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "role",
        [AppRole.STAFF, AppRole.SUPERADMIN],
    )
    @pytest.mark.django_db
    def test_app_admins_see_all_objects(self, site_visibility, obj_visibility, role):
        user = get_app_admin(role)
        site = SiteFactory.create(visibility=site_visibility)
        obj = ControlledSiteContentFactory.build(site=site, visibility=obj_visibility)

        assert view.is_visible_object(user, obj)


class TestHasVisibleSite:
    @pytest.mark.parametrize("get_user", [get_anonymous_user, get_non_member_user])
    @pytest.mark.django_db
    def test_non_members_see_public_site(self, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert view.has_visible_site(user, obj)

    @pytest.mark.parametrize(
        "visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize("get_user", [get_anonymous_user, get_non_member_user])
    @pytest.mark.django_db
    def test_non_members_blocked_for_private_sites(self, visibility, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=visibility)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert view.has_visible_site(user, obj) is False

    @pytest.mark.parametrize(
        "site_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS],
    )
    @pytest.mark.django_db
    def test_members_see_non_team_sites(self, site_visibility):
        (site, user) = get_site_with_member(site_visibility, Role.MEMBER)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert view.has_visible_site(user, obj)

    @pytest.mark.django_db
    def test_members_blocked_for_team_sites(self):
        (site, user) = get_site_with_member(Visibility.TEAM, Role.MEMBER)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert view.has_visible_site(user, obj) is False

    @pytest.mark.parametrize(
        "site_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "role",
        [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.django_db
    def test_team_see_own_site(self, site_visibility, role):
        (site, user) = get_site_with_member(site_visibility, role)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert view.has_visible_site(user, obj)

    @pytest.mark.parametrize(
        "role",
        [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.django_db
    def test_team_see_other_public_sites(self, role):
        (site, user) = get_site_with_member(Visibility.TEAM, role)

        site2 = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = UncontrolledSiteContentFactory.build(site=site2)
        assert view.has_visible_site(user, obj)

    @pytest.mark.parametrize(
        "site_visibility",
        [Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "role",
        [Role.ASSISTANT, Role.EDITOR, Role.LANGUAGE_ADMIN],
    )
    @pytest.mark.django_db
    def test_team_blocked_for_other_private_sites(self, site_visibility, role):
        user = UserFactory.create()
        site = SiteFactory.create()
        MembershipFactory.create(user=user, site=site, role=role)

        site2 = SiteFactory.create(visibility=site_visibility)
        obj = UncontrolledSiteContentFactory.build(site=site2)
        assert not view.has_visible_site(user, obj)

    @pytest.mark.parametrize(
        "site_visibility",
        [Visibility.PUBLIC, Visibility.MEMBERS, Visibility.TEAM],
    )
    @pytest.mark.parametrize(
        "role",
        [AppRole.STAFF, AppRole.SUPERADMIN],
    )
    @pytest.mark.django_db
    def test_app_admins_see_all_sites(self, site_visibility, role):
        user = get_app_admin(role)
        site = SiteFactory.create(visibility=site_visibility)
        obj = UncontrolledSiteContentFactory.build(site=site)

        assert view.has_visible_site(user, obj)
