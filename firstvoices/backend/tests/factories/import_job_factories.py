import factory
from factory.django import DjangoModelFactory

from backend.models.import_jobs import ImportJob, ImportJobReport, ImportJobReportRow
from backend.tests.factories.access import SiteFactory, UserFactory
from backend.tests.factories.media_factories import FileFactory


class ImportJobReportFactory(DjangoModelFactory):
    class Meta:
        model = ImportJobReport

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)

    total_rows = factory.Sequence(int)
    totals = factory.Sequence(lambda n: "{ 'value': %03d }" % n)


class ImportJobReportRowFactory(DjangoModelFactory):
    class Meta:
        model = ImportJobReportRow

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)

    row_number = factory.Sequence(int)
    report = factory.SubFactory(ImportJobReportFactory)
    identifier_field = factory.Sequence(lambda n: "identifier_field %03d" % n)
    identifier_value = factory.Sequence(lambda n: "identifier_value %03d" % n)


class ImportJob(DjangoModelFactory):
    class Meta:
        model = ImportJob

    description = factory.Sequence(lambda n: "description %03d" % n)
    data = factory.SubFactory(FileFactory)
    validation_report = factory.SubFactory(ImportJobReportFactory)
