import factory
import pytest
from factory.django import DjangoModelFactory

from backend.models import DictionaryEntry
from backend.models.constants import Role, Visibility
from backend.tests import factories


class BaseModelFactory(DjangoModelFactory):
    created_by = factory.SubFactory(factories.UserFactory)
    last_modified_by = factory.SubFactory(factories.UserFactory)


class SiteContentFactory(BaseModelFactory):
    title = factory.Sequence(lambda n: "Model %03d" % n)
    site = factory.SubFactory(factories.SiteFactory)


class DictionaryEntryFactory(SiteContentFactory):
    class Meta:
        model = DictionaryEntry


class TestPermissionManager:
    def generate_sites_with_test_data(self, model_factory, user):
        sites = []
        for site_visibility in Visibility:
            # create a site with a membership
            site1 = factories.SiteFactory.create(visibility=site_visibility)
            factories.MembershipFactory(site=site1, user=user)
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

    @pytest.mark.parametrize("model_info", [(DictionaryEntry, DictionaryEntryFactory)])
    @pytest.mark.parametrize(
        "user_role",
        Role,
    )
    @pytest.mark.django_db
    def test_manager_matches_permissions_for_all_sites(self, model_info, user_role):
        model = model_info[0]
        model_factory = model_info[1]

        user = factories.get_non_member_user()
        self.generate_sites_with_test_data(model_factory, user)

        permitted_objects_by_iteration = [
            obj.id
            for obj in model.objects.all()
            if user.has_perm(obj.get_perm("view"), obj)
        ]

        permitted_objects_by_manager = model.objects.all().get_visible_for_user(user)
        assert permitted_objects_by_manager == permitted_objects_by_iteration

        permitted_objects_by_filter = model.objects.filter(
            model.objects.get_visible_filter(user)
        )
        assert permitted_objects_by_filter == permitted_objects_by_iteration

    @pytest.mark.parametrize("model_info", [(DictionaryEntry, DictionaryEntryFactory)])
    @pytest.mark.parametrize(
        "user_role",
        Role,
    )
    @pytest.mark.django_db
    def test_manager_matches_permissions_for_one_site(self, model_info, user_role):
        model = model_info[0]
        model_factory = model_info[1]

        user = factories.get_non_member_user()
        sites = self.generate_sites_with_test_data(model_factory, user)

        for s in sites:
            permitted_objects_by_iteration = [
                obj.id
                for obj in model.objects.filter(site_slug=s.slug)
                if user.has_perm(obj.get_perm("view"), obj)
            ]

            permitted_objects_by_manager = model.objects.get_visible_for_user(user, [s])
            assert permitted_objects_by_manager == permitted_objects_by_iteration

            permitted_objects_by_filter = model.objects.filter(
                model.objects.get_visible_filter(user, [s])
            )
            assert permitted_objects_by_filter == permitted_objects_by_iteration
