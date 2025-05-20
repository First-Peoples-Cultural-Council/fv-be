import factory

from backend.models import BulkVisibilityJob, DictionaryCleanupJob, MTDExportJob
from backend.tests.factories.base_factories import SiteContentFactory


class DictionaryCleanupJobFactory(SiteContentFactory):
    class Meta:
        model = DictionaryCleanupJob


class BulkVisibilityJobFactory(SiteContentFactory):
    class Meta:
        model = BulkVisibilityJob

    task_id = factory.sequence(lambda n: f"task_id_{n}")


class MTDExportJobFactory(SiteContentFactory):
    class Meta:
        model = MTDExportJob
