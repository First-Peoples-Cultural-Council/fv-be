import json

import pytest

from backend.models.constants import Role, Visibility
from backend.tests import factories
from backend.tests.test_apis.base.base_api_test import WriteApiTestMixin
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentCreateApiTestMixin,
    SiteContentDestroyApiTestMixin,
    SiteContentDetailApiTestMixin,
    SiteContentListApiTestMixin,
    SiteContentPatchApiTestMixin,
    SiteContentUpdateApiTestMixin,
)


class ControlledListApiTestMixin(SiteContentListApiTestMixin):
    """
    For use with BaseSiteContentApiTest. Additional test cases for items with their own visibility settings, suitable
    for testing APIs related to BaseControlledSiteContentModel.
    """

    @pytest.mark.django_db
    def test_list_permissions(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.PUBLIC)
        self.create_minimal_instance(site=site, visibility=Visibility.MEMBERS)
        self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(self.get_list_endpoint(site_slug=site.slug))

        assert response.status_code == 200

        response_data = json.loads(response.content)
        assert response_data["count"] == 1
        assert len(response_data["results"]) == 1

        assert response_data["results"][
            0
        ] == self.get_expected_list_response_item_no_email_access(instance, site)


class ControlledDetailApiTestMixin(SiteContentDetailApiTestMixin):
    """
    For use with BaseSiteContentApiTest. Additional test cases for items with their own visibility settings, suitable
    for testing APIs related to BaseControlledSiteContentModel.
    """

    def get_expected_controlled_standard_fields(self, instance, site):
        standard_fields = self.get_expected_entry_standard_fields(instance, site)
        return {
            **standard_fields,
            "visibility": instance.get_visibility_display().lower(),
        }

    @pytest.mark.django_db
    def test_detail_403_entry_not_visible(self):
        site = self.create_site_with_non_member(Visibility.PUBLIC)

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        response = self.client.get(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            )
        )

        assert response.status_code == 403


class ControlledSiteContentCreateApiTestMixin(SiteContentCreateApiTestMixin):
    """
    For use with BaseSiteContentApiTest. Additional test cases for items with their own visibility settings, suitable
    for testing APIs related to BaseControlledSiteContentModel.
    """

    @pytest.mark.django_db
    def test_create_assistant_permissions_valid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)
        data["visibility"] = "team"

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 201

    @pytest.mark.django_db
    def test_create_assistant_permissions_invalid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)
        data["visibility"] = "public"

        response = self.client.post(
            self.get_list_endpoint(site_slug=site.slug),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 403


class ControlledSiteContentUpdateApiTestMixin(SiteContentUpdateApiTestMixin):
    """
    For use with BaseSiteContentApiTest. Additional test cases for items with their own visibility settings, suitable
    for testing APIs related to BaseControlledSiteContentModel.
    """

    @pytest.mark.django_db
    def test_update_assistant_permissions_valid(self):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)
        data["visibility"] = Visibility.TEAM.name

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "visibility", [Visibility.MEMBERS.name, Visibility.PUBLIC.name]
    )
    def test_update_assistant_permissions_invalid(self, visibility):
        site, user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
        )

        instance = self.create_minimal_instance(site=site, visibility=Visibility.TEAM)

        self.client.force_authenticate(user=user)

        data = self.get_valid_data(site)
        data["visibility"] = visibility

        response = self.client.put(
            self.get_detail_endpoint(
                key=self.get_lookup_key(instance), site_slug=site.slug
            ),
            data=self.format_upload_data(data),
            content_type=self.content_type,
        )

        assert response.status_code == 403

        @pytest.mark.django_db
        @pytest.mark.parametrize("visibility", [None, Visibility.TEAM.name])
        def test_patch_assistant_permissions_valid(self, visibility):
            site, user = factories.get_site_with_member(
                site_visibility=Visibility.PUBLIC, user_role=Role.ASSISTANT
            )

            instance = self.create_minimal_instance(
                site=site, visibility=Visibility.TEAM
            )

            self.client.force_authenticate(user=user)

            data = self.get_valid_data(site)
            data["visibility"] = visibility

            response = self.client.patch(
                self.get_detail_endpoint(
                    key=self.get_lookup_key(instance), site_slug=site.slug
                ),
                data=self.format_upload_data(data),
                content_type=self.content_type,
            )

            assert response.status_code == 200


class BaseReadOnlyControlledSiteContentApiTest(
    ControlledListApiTestMixin,
    ControlledDetailApiTestMixin,
    BaseSiteContentApiTest,
):
    pass


class BaseControlledLanguageAdminOnlySiteContentAPITest(
    ControlledListApiTestMixin,
    ControlledDetailApiTestMixin,
    BaseSiteContentApiTest,
):
    pass


class BaseControlledSiteContentApiTest(
    WriteApiTestMixin,
    ControlledSiteContentCreateApiTestMixin,
    ControlledSiteContentUpdateApiTestMixin,
    SiteContentPatchApiTestMixin,
    SiteContentDestroyApiTestMixin,
    ControlledListApiTestMixin,
    ControlledDetailApiTestMixin,
    BaseSiteContentApiTest,
):
    pass
