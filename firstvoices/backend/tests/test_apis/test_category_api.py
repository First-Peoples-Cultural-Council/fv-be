import json

import pytest
from rest_framework.test import APIClient

from backend.models.constants import AppRole
from backend.tests.factories import (
    ChildCategoryFactory,
    ParentCategoryFactory,
    SiteFactory,
    get_app_admin,
)
from backend.tests.test_apis.base_api_test import BaseSiteContentApiTest


class TestCategoryEndpoints(BaseSiteContentApiTest):
    """
    End-to-end tests that the category endpoints have the expected behaviour.
    """

    API_LIST_VIEW = "api:category-list"
    API_DETAIL_VIEW = "api:category-detail"

    def setup_method(self):
        self.client = APIClient()
        self.user = get_app_admin(AppRole.STAFF)
        self.client.force_authenticate(user=self.user)
        self.site = SiteFactory.create()

    @pytest.mark.django_db
    def test_list_empty(self):
        """
        Since categories are always generated when a site is initialized. Thus, there will generally not be a case
        where an empty category list exists. Overriding this test case from baseclass and marking it passed.
        """
        pass

    @pytest.mark.django_db
    def test_category_list_full(self):
        """Assuming a new site will have at least 1 category."""

        response = self.client.get(self.get_list_endpoint(self.site.slug))
        response_data = json.loads(response.content)

        assert response.status_code == 200
        assert response_data["count"] > 0

        category_json = response_data["results"][0]
        # Testing general structure of the response json.
        # Specific testing done in the retrieve view test
        assert "id" in category_json
        assert "title" in category_json
        assert "children" in category_json
        assert isinstance(category_json["children"], list)
        assert "description" in category_json

    @pytest.mark.django_db
    def test_detail_parent_category(self):
        parent_category = ParentCategoryFactory.create(site=self.site)
        child_category = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )
        detail_endpoint = self.get_detail_endpoint(self.site.slug, parent_category.id)
        response = self.client.get(detail_endpoint)

        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {
            "id": str(parent_category.id),
            "title": parent_category.title,
            "description": parent_category.description,
            "children": [
                {
                    "id": str(child_category.id),
                    "title": child_category.title,
                    "description": child_category.description,
                }
            ],
            "parent": None,
        }

    @pytest.mark.django_db
    def test_detail_children_category(self):
        parent_category = ParentCategoryFactory.create(site=self.site)
        child_category = ChildCategoryFactory.create(
            site=self.site, parent=parent_category
        )

        detail_endpoint = self.get_detail_endpoint(self.site.slug, child_category.id)

        response = self.client.get(detail_endpoint)
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data == {
            "id": str(child_category.id),
            "title": child_category.title,
            "description": child_category.description,
            "children": [],
            "parent": str(parent_category.id),
        }

    @pytest.mark.django_db
    def test_detail_404(self):
        wrong_endpoint = self.get_detail_endpoint(self.site.slug, "54321")
        response = self.client.get(wrong_endpoint)
        assert response.status_code == 404
