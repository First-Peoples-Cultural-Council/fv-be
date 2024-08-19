import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.permissions.predicates import edit
from backend.tests.factories import (
    ControlledSiteContentFactory,
    SiteFactory,
    UncontrolledSiteContentFactory,
    get_anonymous_user,
    get_app_admin,
    get_non_member_user,
    get_site_with_member,
)


class TestEditRolePredicates:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "predicate",
        [
            edit.is_at_least_assistant_or_super,
            edit.is_at_least_editor_or_super,
            edit.is_language_admin_or_super,
        ],
    )
    def test_superadmin_can_edit(self, predicate):
        user = get_app_admin(AppRole.SUPERADMIN)
        obj = SiteFactory.create()
        assert predicate(user, obj)

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "predicate",
        [
            edit.is_at_least_assistant_or_super,
            edit.is_at_least_editor_or_super,
            edit.is_language_admin_or_super,
        ],
    )
    def test_staff_admin_can_not_edit(self, predicate):
        user = get_app_admin(AppRole.STAFF)
        obj = SiteFactory.create()
        assert not predicate(user, obj)


def get_member_of_other_site():
    _, user = get_site_with_member(Visibility.PUBLIC, Role.LANGUAGE_ADMIN)
    return user


class TestCanDeleteCoreUncontrolledData:
    @pytest.mark.parametrize(
        "get_user", [get_anonymous_user, get_non_member_user, get_member_of_other_site]
    )
    @pytest.mark.django_db
    def test_non_members_blocked(self, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert not edit.can_delete_media(user, obj)

    @pytest.mark.django_db
    def test_members_blocked(self):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.MEMBER)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert not edit.can_delete_media(user, obj)

    @pytest.mark.django_db
    def test_staff_admin_blocked(self):
        user = get_app_admin(AppRole.STAFF)
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert not edit.can_delete_media(user, obj)

    @pytest.mark.parametrize("role", [Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_editors_and_up_permitted(self, role):
        site, user = get_site_with_member(Visibility.PUBLIC, role)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert edit.can_delete_media(user, obj)

    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_assistant_blocked_for_non_team_data(self, visibility):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.ASSISTANT)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert not edit.can_delete_media(user, obj)

    @pytest.mark.django_db
    def test_assistant_permitted_for_team_data(self):
        site, user = get_site_with_member(Visibility.TEAM, Role.ASSISTANT)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert edit.can_delete_media(user, obj)

    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_assistant_blocked_for_edited_non_team_data(self, visibility):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.ASSISTANT)
        obj = UncontrolledSiteContentFactory.create(site=site)
        site.visibility = Visibility.TEAM
        assert not edit.can_delete_media(user, obj)


class TestCanEditControlledData:
    @pytest.mark.parametrize(
        "get_user", [get_anonymous_user, get_non_member_user, get_member_of_other_site]
    )
    @pytest.mark.django_db
    def test_non_members_blocked(self, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(site=site)
        assert not edit.can_edit_controlled_data(user, obj)

    @pytest.mark.django_db
    def test_members_blocked(self):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.MEMBER)
        obj = ControlledSiteContentFactory.create(site=site)
        assert not edit.can_edit_controlled_data(user, obj)

    @pytest.mark.django_db
    def test_staff_admin_blocked(self):
        user = get_app_admin(AppRole.STAFF)
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = ControlledSiteContentFactory.create(site=site)
        assert not edit.can_edit_controlled_data(user, obj)

    @pytest.mark.parametrize("role", [Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_editors_and_up_permitted(self, role):
        site, user = get_site_with_member(Visibility.PUBLIC, role)
        obj = ControlledSiteContentFactory.create(site=site)
        assert edit.can_edit_controlled_data(user, obj)

    @pytest.mark.django_db
    def test_assistant_permitted_for_team_data(self):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.ASSISTANT)
        obj = ControlledSiteContentFactory.create(site=site, visibility=Visibility.TEAM)
        assert edit.can_edit_controlled_data(user, obj)

    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_assistant_blocked_for_editing_non_team_data(self, visibility):
        site, user = get_site_with_member(Visibility.TEAM, Role.ASSISTANT)
        obj = ControlledSiteContentFactory.create(site=site, visibility=visibility)
        assert not edit.can_edit_controlled_data(user, obj)
