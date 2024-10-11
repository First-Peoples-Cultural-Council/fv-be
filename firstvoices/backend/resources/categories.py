from backend.models.category import Category
from backend.resources.base import SiteContentResource


class CategoryResource(SiteContentResource):
    class Meta:
        model = Category


class CategoryMigrationResource(CategoryResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        if not dry_run:
            # If there are categories to be imported, only then remove previous categories
            if len(dataset):
                Category.objects.filter(site__id__in=dataset["site"]).delete()
