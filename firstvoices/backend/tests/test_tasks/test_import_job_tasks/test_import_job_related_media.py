import pytest


@pytest.mark.django_db
class TestImportJobRelatedMedia:
    MIMETYPE = "text/csv"
    CSV_FILES_DIR = "test_tasks/test_import_job_tasks/resources"
