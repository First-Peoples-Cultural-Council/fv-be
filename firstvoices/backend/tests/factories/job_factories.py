import factory

from backend.models import BulkVisibilityJob, DictionaryCleanupJob, MTDExportJob
from backend.models.jobs import ExportJob
from backend.tests.factories.base_factories import BaseSiteContentFactory


class DictionaryCleanupJobFactory(BaseSiteContentFactory):
    class Meta:
        model = DictionaryCleanupJob


class BulkVisibilityJobFactory(BaseSiteContentFactory):
    class Meta:
        model = BulkVisibilityJob

    task_id = factory.sequence(lambda n: f"task_id_{n}")


class MTDExportJobFactory(BaseSiteContentFactory):
    class Meta:
        model = MTDExportJob


class ExportJobFactory(BaseSiteContentFactory):
    class Meta:
        model = ExportJob
