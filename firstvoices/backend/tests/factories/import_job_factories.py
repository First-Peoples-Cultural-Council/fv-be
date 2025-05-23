import factory

from backend.models.import_jobs import ImportJob, ImportJobReport, ImportJobReportRow
from backend.tests.factories.base_factories import BaseSiteContentFactory
from backend.tests.factories.media_factories import FileFactory


class ImportJobReportFactory(BaseSiteContentFactory):
    class Meta:
        model = ImportJobReport


class ImportJobReportRowFactory(BaseSiteContentFactory):
    class Meta:
        model = ImportJobReportRow

    row_number = factory.Sequence(int)
    report = factory.SubFactory(ImportJobReportFactory)
    identifier_field = factory.Sequence(lambda n: "identifier_field %03d" % n)
    identifier_value = factory.Sequence(lambda n: "identifier_value %03d" % n)


class ImportJobFactory(BaseSiteContentFactory):
    class Meta:
        model = ImportJob

    title = factory.Sequence(lambda n: "title %03d" % n)
    data = factory.SubFactory(FileFactory)
