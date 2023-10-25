import uuid

import pytest
import tablib

from backend.models.category import Category
from backend.resources.categories import CategoryMigrationResource, CategoryResource
from backend.tests.factories import SiteFactory, UserFactory


def build_table(data):
    headers = [
        "id,created,created_by,last_modified,last_modified_by,title,description,parent,site"
    ]
    table = tablib.import_set("\n".join(headers + data), format="csv")
    return table


@pytest.mark.skip("Tests are for initial migration only")
class TestCategoryImport:
    def setup(self):
        self.site1 = SiteFactory.create()
        self.user1 = UserFactory.create()
        test_category_1_id = uuid.uuid4()
        test_category_2_id = uuid.uuid4()
        data = [
            f"{test_category_1_id},2023-02-02 21:21:10.713,{self.user1.email},2023-02-02 21:21:39.864,"
            f"{self.user1.email},testCategory1,test description for the category,,{self.site1.id}",
            f"{test_category_2_id},2023-02-02 21:21:10.713,{self.user1.email},2023-02-02 21:21:39.864,"
            f"{self.user1.email},testCategory2,test description for the category,{test_category_1_id},{self.site1.id}",
        ]
        self.table = build_table(data)

    @pytest.mark.django_db
    def test_import_base_data(self):
        result = CategoryResource().import_data(dataset=self.table)
        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 2

        imported_category = Category.objects.get(
            site__id=self.site1.id, title="testCategory1"
        )
        assert imported_category.title == self.table["title"][0]
        assert imported_category.description == self.table["description"][0]
        assert imported_category.parent is None

    @pytest.mark.django_db
    def test_delete_previous_categories(self):
        result = CategoryMigrationResource().import_data(dataset=self.table)
        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 2

        categories_count = Category.objects.filter(site__id=self.site1.id).count()
        assert categories_count == 2

    @pytest.mark.django_db
    def test_parent_relation(self):
        result = CategoryMigrationResource().import_data(dataset=self.table)
        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 2

        imported_category_1 = Category.objects.get(
            site__id=self.site1.id, title="testCategory1"
        )
        imported_category_2 = Category.objects.get(
            site__id=self.site1.id, title="testCategory2"
        )

        assert imported_category_2.parent_id == imported_category_1.id
