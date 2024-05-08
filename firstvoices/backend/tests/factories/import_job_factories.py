import factory
from django.db.models import signals
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


# Muting signals, as related tasks are tested separately
@factory.django.mute_signals(signals.post_save)
class ImportJobFactory(DjangoModelFactory):
    class Meta:
        model = ImportJob

    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)

    title = factory.Sequence(lambda n: "title %03d" % n)
    data = factory.SubFactory(FileFactory)
    validation_report = factory.SubFactory(ImportJobReportFactory)
