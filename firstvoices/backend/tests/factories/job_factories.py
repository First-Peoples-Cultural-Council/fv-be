import factory
from factory.django import DjangoModelFactory

from backend.models import BulkVisibilityJob, DictionaryCleanupJob, MTDExportJob
from backend.tests.factories.access import SiteFactory, UserFactory


class DictionaryCleanupJobFactory(DjangoModelFactory):
    class Meta:
        model = DictionaryCleanupJob

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)


class BulkVisibilityJobFactory(DjangoModelFactory):
    class Meta:
        model = BulkVisibilityJob

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)

    task_id = factory.sequence(lambda n: f"task_id_{n}")


class MTDExportJobFactory(DjangoModelFactory):
    class Meta:
        model = MTDExportJob

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
