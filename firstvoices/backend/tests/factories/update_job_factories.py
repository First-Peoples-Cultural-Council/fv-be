import factory

from backend.models.update_jobs import UpdateJob, UpdateJobReport, UpdateJobReportRow
from backend.tests.factories.base_factories import BaseSiteContentFactory
from backend.tests.factories.media_factories import FileFactory


class UpdateJobReportFactory(BaseSiteContentFactory):
    class Meta:
        model = UpdateJobReport


class UpdateJobReportRowFactory(BaseSiteContentFactory):
    class Meta:
        model = UpdateJobReportRow

    row_number = factory.Sequence(int)
    report = factory.SubFactory(UpdateJobReportFactory)
    identifier_field = factory.Sequence(lambda n: "identifier_field %03d" % n)
    identifier_value = factory.Sequence(lambda n: "identifier_value %03d" % n)


class UpdateJobFactory(BaseSiteContentFactory):
    class Meta:
        model = UpdateJob

    title = factory.Sequence(lambda n: "title %03d" % n)
    data = factory.SubFactory(FileFactory)
