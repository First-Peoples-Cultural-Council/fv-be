import pytest

from backend.models.constants import Visibility
from backend.tasks.import_job_tasks import execute_dry_run_import
from backend.tests.factories import FileFactory, ImportJobFactory, SiteFactory
from backend.tests.utils import get_sample_file


class TestDryRunImport:
    MIMETYPE = "text/csv"

    @pytest.mark.django_db
    def test_base_case_dictionary_entries(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        file_content = get_sample_file("import_job_minimal.csv", self.MIMETYPE)
        file = FileFactory(content=file_content)

        import_job_instance = ImportJobFactory(site=site, data=file)

        # Manually executing task instead of through signals
        execute_dry_run_import(import_job_instance)

        validation_report = import_job_instance.validation_report

        assert validation_report.new_rows == 2
        assert validation_report.error_rows == 0
        assert validation_report.skipped_rows == 0

    # @pytest.mark.django_db
    # def test_all_columns_dictionary_entries(self):
    #     # Only testing for MVP columns now.
    #     # More columns should be added to this file/test
    #     # as we start supporting more columns, e.g. related_media
    #
    #     filepath = '../../../test_upload_all_columns_valid.csv'
    #     site = SiteFactory(visibility=Visibility.PUBLIC)
    #     execute_dry_run_import(filepath, site)
