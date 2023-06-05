import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.permissions.predicates import edit2
from backend.tests.factories import (
    SiteFactory,
    UncontrolledSiteContentFactory,
    get_anonymous_user,
    get_app_admin,
    get_non_member_user,
    get_site_with_member,
)


def get_member_of_other_site():
    _, user = get_site_with_member(Visibility.PUBLIC, Role.LANGUAGE_ADMIN)
    return user


class TestCanEditCoreUncontrolledData:
    @pytest.mark.parametrize(
        "get_user", [get_anonymous_user, get_non_member_user, get_member_of_other_site]
    )
    @pytest.mark.django_db
    def test_non_members_blocked(self, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert not edit2.can_edit_core_uncontrolled_data(user, obj)

    @pytest.mark.django_db
    def test_members_blocked(self):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.MEMBER)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert not edit2.can_edit_core_uncontrolled_data(user, obj)

    @pytest.mark.django_db
    def test_staff_admin_blocked(self):
        user = get_app_admin(AppRole.STAFF)
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert not edit2.can_edit_core_uncontrolled_data(user, obj)

    @pytest.mark.parametrize("role", [Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_editors_and_up_permitted(self, role):
        site, user = get_site_with_member(Visibility.PUBLIC, role)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert edit2.can_edit_core_uncontrolled_data(user, obj)

    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_assistant_blocked_for_non_team_data(self, visibility):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.ASSISTANT)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert not edit2.can_edit_core_uncontrolled_data(user, obj)

    @pytest.mark.django_db
    def test_assistant_permitted_for_team_data(self):
        site, user = get_site_with_member(Visibility.TEAM, Role.ASSISTANT)
        obj = UncontrolledSiteContentFactory.create(site=site)
        assert edit2.can_edit_core_uncontrolled_data(user, obj)

    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_assistant_blocked_for_edited_non_team_data(self, visibility):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.ASSISTANT)
        obj = UncontrolledSiteContentFactory.create(site=site)
        site.visibility = Visibility.TEAM
        assert not edit2.can_edit_core_uncontrolled_data(user, obj)


class TestCanAddCoreUncontrolledData:
    @pytest.mark.parametrize(
        "get_user", [get_anonymous_user, get_non_member_user, get_member_of_other_site]
    )
    @pytest.mark.django_db
    def test_non_members_blocked(self, get_user):
        user = get_user()
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert not edit2.can_add_core_uncontrolled_data(user, obj)

    @pytest.mark.django_db
    def test_members_blocked(self):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.MEMBER)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert not edit2.can_add_core_uncontrolled_data(user, obj)

    @pytest.mark.django_db
    def test_staff_admin_blocked(self):
        user = get_app_admin(AppRole.STAFF)
        site = SiteFactory.create(visibility=Visibility.PUBLIC)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert not edit2.can_add_core_uncontrolled_data(user, obj)

    @pytest.mark.parametrize("role", [Role.EDITOR, Role.LANGUAGE_ADMIN])
    @pytest.mark.django_db
    def test_editors_and_up_permitted(self, role):
        site, user = get_site_with_member(Visibility.PUBLIC, role)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert edit2.can_add_core_uncontrolled_data(user, obj)

    @pytest.mark.parametrize("visibility", [Visibility.PUBLIC, Visibility.MEMBERS])
    @pytest.mark.django_db
    def test_assistant_blocked_for_non_team_data(self, visibility):
        site, user = get_site_with_member(Visibility.PUBLIC, Role.ASSISTANT)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert not edit2.can_add_core_uncontrolled_data(user, obj)

    @pytest.mark.django_db
    def test_assistant_permitted_for_team_data(self):
        site, user = get_site_with_member(Visibility.TEAM, Role.ASSISTANT)
        obj = UncontrolledSiteContentFactory.build(site=site)
        assert edit2.can_add_core_uncontrolled_data(user, obj)
