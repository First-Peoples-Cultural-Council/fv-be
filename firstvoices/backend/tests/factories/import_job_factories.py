import factory

from backend.models.batch_job_utils import BatchJobReport, BatchJobReportRow
from backend.models.import_jobs import ImportJob
from backend.tests.factories.base_factories import BaseSiteContentFactory
from backend.tests.factories.media_factories import FileFactory


class BatchJobReportFactory(BaseSiteContentFactory):
    class Meta:
        model = BatchJobReport


class BatchJobReportRowFactory(BaseSiteContentFactory):
    class Meta:
        model = BatchJobReportRow

    row_number = factory.Sequence(int)
    report = factory.SubFactory(BatchJobReportFactory)
    identifier_field = factory.Sequence(lambda n: "identifier_field %03d" % n)
    identifier_value = factory.Sequence(lambda n: "identifier_value %03d" % n)


class ImportJobFactory(BaseSiteContentFactory):
    class Meta:
        model = ImportJob

    title = factory.Sequence(lambda n: "title %03d" % n)
    data = factory.SubFactory(FileFactory)
