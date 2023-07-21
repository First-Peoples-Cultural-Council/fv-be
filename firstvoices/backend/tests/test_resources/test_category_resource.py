import uuid

import pytest
import tablib

from backend.models.category import Category
from backend.resources.categories import CategoryMigrationResource, CategoryResource
from backend.tests.factories import SiteFactory, UserFactory


def build_table(data):
    headers = [
        "id,created,created_by,last_modified,last_modified_by,title,visibility,description,parent,site"
    ]
    table = tablib.import_set("\n".join(headers + data), format="csv")
    return table


class TestCategoryImport:
    def setup(self):
        self.site1 = SiteFactory.create()
        self.user1 = UserFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,{self.user1.email},2023-02-02 21:21:39.864,"
            f"{self.user1.email},testCategory,Public,,,{self.site1.id}"
        ]
        self.table = build_table(data)

    @pytest.mark.django_db
    def test_import_base_data(self):
        result = CategoryResource().import_data(dataset=self.table)
        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 1

        imported_category = Category.objects.get(
            site__id=self.site1.id, title="testCategory"
        )
        assert imported_category.title == self.table["title"][0]

    @pytest.mark.django_db
    def test_delete_previous_categories(self):
        result = CategoryMigrationResource().import_data(dataset=self.table)
        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 1

        categories_count = Category.objects.filter(site__id=self.site1.id).count()
        assert categories_count == 1
