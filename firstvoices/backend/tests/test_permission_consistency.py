import factory
import pytest
from factory.django import DjangoModelFactory

from backend.models import Category, DictionaryEntry
from backend.models.constants import AppRole, Role, Visibility
from backend.tests import factories


class BaseModelFactory(DjangoModelFactory):
    created_by = factory.SubFactory(factories.UserFactory)
    last_modified_by = factory.SubFactory(factories.UserFactory)


class SiteContentFactory(BaseModelFactory):
    title = factory.Sequence(lambda n: "Model %03d" % n)
    site = factory.SubFactory(factories.SiteFactory)


class CategoryFactory(SiteContentFactory):
    class Meta:
        model = Category


def get_permitted_ids(user, queryset):
    return {obj.id for obj in queryset if user.has_perm(obj.get_perm("view"), obj)}


class TestSiteContentPermissionManager:
    model_info_values = [(Category, CategoryFactory)]
    model_names = ["Category"]

    @pytest.mark.parametrize(
        "model_info",
        model_info_values,
        ids=model_names,
    )
    @pytest.mark.parametrize("user_role", Role, ids=Role.names)
    @pytest.mark.django_db
    def test_visible(self, model_info, user_role):
        user = factories.get_non_member_user()

        self.assert_visible_matches(model_info, user, user_role)

    @pytest.mark.parametrize(
        "model_info",
        model_info_values,
        ids=model_names,
    )
    @pytest.mark.parametrize("app_role", AppRole, ids=AppRole.names)
    @pytest.mark.django_db
    def test_visible_for_superadmins(self, model_info, app_role):
        user = factories.get_non_member_user()
        factories.AppMembershipFactory.create(user=user, role=app_role)

        self.assert_visible_matches(model_info, user, Role.MEMBER)

    def assert_visible_matches(self, model_info, user, user_role):
        model = model_info[0]
        model_factory = model_info[1]
        self.generate_sites_with_test_data(model_factory, user, user_role)
        visible_by_permission_rules = get_permitted_ids(user, model.objects.all())
        visible_by_permission_manager = {obj.id for obj in model.objects.visible(user)}
        assert visible_by_permission_manager == visible_by_permission_rules
        visible_by_permission_filter = {
            obj.id
            for obj in model.objects.filter(model.objects.visible_as_filter(user))
        }
        assert visible_by_permission_filter == visible_by_permission_rules

    @pytest.mark.parametrize(
        "model_info",
        model_info_values,
        ids=model_names,
    )
    @pytest.mark.parametrize("user_role", Role, ids=Role.names)
    @pytest.mark.django_db
    def test_visible_by_site(self, model_info, user_role):
        user = factories.get_non_member_user()

        self.assert_visible_by_site(model_info, user, user_role)

    @pytest.mark.parametrize(
        "model_info",
        model_info_values,
        ids=model_names,
    )
    @pytest.mark.parametrize("app_role", AppRole, ids=AppRole.names)
    @pytest.mark.django_db
    def test_visible_by_site_for_superadmins(self, model_info, app_role):
        user = factories.get_non_member_user()
        factories.AppMembershipFactory.create(user=user, role=app_role)

        self.assert_visible_by_site(model_info, user, Role.MEMBER)

    def assert_visible_by_site(self, model_info, user, user_role):
        model = model_info[0]
        model_factory = model_info[1]
        sites = self.generate_sites_with_test_data(model_factory, user, user_role)
        for s in sites:
            visible_by_permission_rules = get_permitted_ids(
                user, model.objects.filter(site=s)
            )

            visible_by_permission_manager = {
                obj.id for obj in model.objects.visible_by_site(user, s)
            }
            assert visible_by_permission_manager == visible_by_permission_rules

            visible_by_permission_filter = {
                obj.id
                for obj in model.objects.filter(
                    model.objects.visible_as_filter(user, s)
                )
            }
            assert visible_by_permission_filter == visible_by_permission_rules

    def generate_sites_with_test_data(self, model_factory, user, user_role):
        sites = []
        for site_visibility in Visibility:
            # create a site with a membership
            site1 = factories.SiteFactory.create(visibility=site_visibility)
            factories.MembershipFactory(site=site1, user=user, role=user_role)
            sites.append(site1)

            # create object in the site
            model_factory.create(site=site1)

            # create a site with no membership
            site2 = factories.SiteFactory.create(visibility=site_visibility)
            sites.append(site2)

            # create object in the site
            model_factory.create(site=site2)

        return sites


class DictionaryEntryFactory(SiteContentFactory):
    class Meta:
        model = DictionaryEntry


class TestControlledSiteContentPermissionManager:
    model_info_values = [(DictionaryEntry, DictionaryEntryFactory)]
    model_names = ["DictionaryEntry"]

    @pytest.mark.parametrize(
        "model_info",
        model_info_values,
        ids=model_names,
    )
    @pytest.mark.parametrize("user_role", Role, ids=Role.names)
    @pytest.mark.django_db
    def test_visible(self, model_info, user_role):
        user = factories.get_non_member_user()

        self.assert_visible_matches(model_info, user, user_role)

    @pytest.mark.parametrize(
        "model_info",
        model_info_values,
        ids=model_names,
    )
    @pytest.mark.parametrize("app_role", AppRole, ids=AppRole.names)
    @pytest.mark.django_db
    def test_visible_for_superadmins(self, model_info, app_role):
        user = factories.get_non_member_user()
        factories.AppMembershipFactory.create(user=user, role=app_role)

        self.assert_visible_matches(model_info, user, Role.MEMBER)

    def assert_visible_matches(self, model_info, user, user_role):
        model = model_info[0]
        model_factory = model_info[1]
        self.generate_sites_with_test_data(model_factory, user, user_role)
        visible_by_permission_rules = get_permitted_ids(user, model.objects.all())
        visible_by_permission_manager = {obj.id for obj in model.objects.visible(user)}
        assert visible_by_permission_manager == visible_by_permission_rules
        visible_by_permission_filter = {
            obj.id
            for obj in model.objects.filter(model.objects.visible_as_filter(user))
        }
        assert visible_by_permission_filter == visible_by_permission_rules

    @pytest.mark.parametrize(
        "model_info",
        model_info_values,
        ids=model_names,
    )
    @pytest.mark.parametrize("user_role", Role, ids=Role.names)
    @pytest.mark.django_db
    def test_visible_by_site(self, model_info, user_role):
        user = factories.get_non_member_user()

        self.assert_visible_by_site(model_info, user, user_role)

    @pytest.mark.parametrize(
        "model_info",
        model_info_values,
        ids=model_names,
    )
    @pytest.mark.parametrize("app_role", AppRole, ids=AppRole.names)
    @pytest.mark.django_db
    def test_visible_by_site_for_superadmins(self, model_info, app_role):
        user = factories.get_non_member_user()
        factories.AppMembershipFactory.create(user=user, role=app_role)

        self.assert_visible_by_site(model_info, user, Role.MEMBER)

    def assert_visible_by_site(self, model_info, user, user_role):
        model = model_info[0]
        model_factory = model_info[1]
        sites = self.generate_sites_with_test_data(model_factory, user, user_role)
        for s in sites:
            visible_by_permission_rules = get_permitted_ids(
                user, model.objects.filter(site=s)
            )

            visible_by_permission_manager = {
                obj.id for obj in model.objects.visible_by_site(user, s)
            }
            assert visible_by_permission_manager == visible_by_permission_rules

            visible_by_permission_filter = {
                obj.id
                for obj in model.objects.filter(
                    model.objects.visible_as_filter(user, s)
                )
            }
            assert visible_by_permission_filter == visible_by_permission_rules

    def generate_sites_with_test_data(self, model_factory, user, user_role):
        sites = []
        for site_visibility in Visibility:
            # create a site with a membership
            site1 = factories.SiteFactory.create(visibility=site_visibility)
            factories.MembershipFactory(site=site1, user=user, role=user_role)
            sites.append(site1)

            # create objects in the site
            for v1 in Visibility:
                model_factory.create(visibility=v1, site=site1)

            # create a site with no membership
            site2 = factories.SiteFactory.create(visibility=site_visibility)
            sites.append(site2)

            # create objects in the site
            for v2 in Visibility:
                model_factory.create(visibility=v2, site=site2)

        return sites
