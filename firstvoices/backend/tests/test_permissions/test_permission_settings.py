import factory
import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from backend.models import Lyric, Page, User
from backend.models.base import BaseControlledSiteContentModel, BaseSiteContentModel
from backend.models.constants import AppRole, Role, Visibility
from backend.models.dictionary import BaseDictionaryContentModel
from backend.tests import factories


class BaseModelFactory(DjangoModelFactory):
    created_by = factory.SubFactory(factories.UserFactory)
    last_modified_by = factory.SubFactory(factories.UserFactory)


class SiteContentFactory(BaseModelFactory):
    site = factory.SubFactory(factories.SiteFactory)


def get_permitted_ids(user, queryset):
    return {obj.id for obj in queryset if user.has_perm(obj.get_perm("view"), obj)}


class TestPermissionManager:
    # test all models
    # ... but skip User until fw-4165

    models = [
        m
        for m in apps.get_app_config("backend").get_models()
        if (m not in (User, Lyric, Page))

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

        visible_by_permission_rules = get_permitted_ids(user, model_cls.objects.all())
        visible_by_permission_manager = {
            obj.id for obj in model_cls.objects.visible(user)
        }
        assert visible_by_permission_manager == visible_by_permission_rules
        visible_by_permission_filter = {
            obj.id
            for obj in model_cls.objects.filter(
                model_cls.objects.visible_as_filter(user)
            )
        }
        assert visible_by_permission_filter == visible_by_permission_rules

    def generate_test_data(self, model_cls, model_factory, user, user_role):
        """
        Attempt to automatically generate the right kind of data. This will sometimes need to be updated
        when we add new kinds of models.
        """

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
