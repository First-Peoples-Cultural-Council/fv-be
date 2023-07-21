from import_export import fields

from backend.models.category import Category
from backend.models.constants import Visibility
from backend.resources.base import BaseResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class CategoryResource(BaseResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    class Meta:
        model = Category


class CategoryMigrationResource(CategoryResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        if not dry_run:
            # If there are categories to be imported, only then remove previous categories
            if len(dataset):
                Category.objects.filter(site__id__in=dataset["site"]).delete()
