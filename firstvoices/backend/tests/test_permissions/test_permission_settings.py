import factory
import pytest
from django.apps import apps
from factory.django import DjangoModelFactory

from backend.models import ImmersionLabel, Lyric, StoryPage
from backend.models.base import BaseControlledSiteContentModel, BaseSiteContentModel
from backend.models.constants import AppRole, Role, Visibility
from backend.models.dictionary import BaseDictionaryContentModel
from backend.tests import factories

"""
This class generates tests for all models (with a few exclusions), to verify that the different forms of view
permissions all have the same effect. (Direct use of predicates, permission rules on the models, and query filters.)
"""


class BaseModelFactory(DjangoModelFactory):
    created_by = factory.SubFactory(factories.UserFactory)
    last_modified_by = factory.SubFactory(factories.UserFactory)


class SiteContentFactory(BaseModelFactory):
    site = factory.SubFactory(factories.SiteFactory)


def get_permitted_ids(user, queryset):
    return [obj.id for obj in queryset if user.has_perm(obj.get_perm("view"), obj)]


def assert_unordered_lists_have_same_items(list1, list2):
    assert len(list1) == len(list2)

    list1_sorted = sorted(list1)
    list2_sorted = sorted(list2)
    assert list1_sorted == list2_sorted


class TestPermissionManager:
    # test all models
    # ... but skip a few

    models = [
        m
        for m in apps.get_app_config("backend").get_models()
        if (m not in (Lyric, StoryPage))
    ]

    @pytest.mark.parametrize(
        "model_cls",
        models,
    )
    @pytest.mark.parametrize("user_role", Role, ids=Role.names)
    @pytest.mark.django_db
    def test_visible(self, model_cls, user_role):
        user = factories.get_non_member_user()

        self.assert_visible_matches(model_cls, user, user_role)

    @pytest.mark.parametrize(
        "model_cls",
        models,
    )
    @pytest.mark.parametrize("app_role", AppRole, ids=AppRole.names)
    @pytest.mark.django_db
    def test_visible_for_superadmins(self, model_cls, app_role):
        user = factories.get_non_member_user()
        factories.AppMembershipFactory.create(user=user, role=app_role)

        self.assert_visible_matches(model_cls, user, Role.MEMBER)

    def get_or_create_factory(self, model_cls):
        if hasattr(factories, "%sFactory" % model_cls.__name__):
            return getattr(factories, "%sFactory" % model_cls.__name__)
        else:
            base_model = (
                SiteContentFactory if hasattr(model_cls, "site") else BaseModelFactory
            )

            class ModelFactory(base_model):
                class Meta:
                    model = model_cls

            return ModelFactory

    def assert_visible_matches(self, model_cls, user, user_role):
        model_factory = self.get_or_create_factory(model_cls)

        self.generate_test_data(model_cls, model_factory, user, user_role)

        # get list via has_perm()
        visible_by_permission_rules = get_permitted_ids(user, model_cls.objects.all())

        # get list via Model.objects.visible()
        visible_by_permission_manager = [
            obj.id for obj in model_cls.objects.visible(user)
        ]

        assert_unordered_lists_have_same_items(
            visible_by_permission_manager, visible_by_permission_rules
        )

        # get list via Model.objects.visible_as_filter()
        visible_by_permission_filter = [
            obj.id
            for obj in model_cls.objects.filter(
                model_cls.objects.visible_as_filter(user)
            ).distinct()
        ]

        assert_unordered_lists_have_same_items(
            visible_by_permission_manager, visible_by_permission_filter
        )

    def generate_test_data(self, model_cls, model_factory, user, user_role):
        """
        Attempt to automatically generate the right kind of data. This will sometimes need to be updated
        when we add new kinds of models.
        """

        if issubclass(model_cls, ImmersionLabel):
            self.generate_immersion_label_test_data(model_factory, user, user_role)
            return

        if issubclass(model_cls, BaseDictionaryContentModel):
            self.generate_dictionary_content_test_data(model_factory, user, user_role)
            return

        if issubclass(model_cls, BaseControlledSiteContentModel):
            self.generate_controlled_site_content_test_data(
                model_factory, user, user_role
            )
            return

        if issubclass(model_cls, BaseSiteContentModel):
            self.generate_site_content_test_data(model_factory, user, user_role)
            return

        # models that use BaseModel
        model_factory.create()

    def generate_site_content_test_data(self, model_factory, user, user_role):
        for site_visibility in Visibility:
            # create a site with a membership
            site1 = factories.SiteFactory.create(visibility=site_visibility)
            factories.MembershipFactory(site=site1, user=user, role=user_role)

            # create object in the site
            model_factory.create(site=site1)

            # create a site with no membership
            site2 = factories.SiteFactory.create(visibility=site_visibility)

            # create object in the site
            model_factory.create(site=site2)

    def generate_controlled_site_content_test_data(
        self, model_factory, user, user_role
    ):
        for site_visibility in Visibility:
            # create a site with a membership
            site1 = factories.SiteFactory.create(visibility=site_visibility)
            factories.MembershipFactory(site=site1, user=user, role=user_role)

            # create objects in the site
            for v1 in Visibility:
                model_factory.create(visibility=v1, site=site1)

            # create a site with no membership
            site2 = factories.SiteFactory.create(visibility=site_visibility)

            # create objects in the site
            for v2 in Visibility:
                model_factory.create(visibility=v2, site=site2)

    def generate_dictionary_content_test_data(self, model_factory, user, user_role):
        for site_visibility in Visibility:
            # create a site with a membership
            site1 = factories.SiteFactory.create(visibility=site_visibility)
            factories.MembershipFactory(site=site1, user=user, role=user_role)

            # create objects in the site
            for v1 in Visibility:
                entry1 = factories.DictionaryEntryFactory.create(
                    site=site1, visibility=v1
                )
                model_factory.create(dictionary_entry=entry1)

            # create a site with no membership
            site2 = factories.SiteFactory.create(visibility=site_visibility)

            # create objects in the site
            for v2 in Visibility:
                entry2 = factories.DictionaryEntryFactory.create(
                    site=site2, visibility=v2
                )
                model_factory.create(dictionary_entry=entry2)

    def generate_immersion_label_test_data(self, model_factory, user, user_role):
        for site_visibility in Visibility:
            # create a site with a membership
            site1 = factories.SiteFactory.create(visibility=site_visibility)
            factories.MembershipFactory(site=site1, user=user, role=user_role)

            # Adding a dictionary entry matching site's visibility
            entry_1 = factories.DictionaryEntryFactory.create(
                site=site1, visibility=site_visibility
            )

            # create object in the site
            model_factory.create(site=site1, dictionary_entry=entry_1)

            # create a site with no membership
            site2 = factories.SiteFactory.create(visibility=site_visibility)
            entry_2 = factories.DictionaryEntryFactory.create(
                site=site2, visibility=site_visibility
            )

            # create object in the site
            model_factory.create(site=site2, dictionary_entry=entry_2)
