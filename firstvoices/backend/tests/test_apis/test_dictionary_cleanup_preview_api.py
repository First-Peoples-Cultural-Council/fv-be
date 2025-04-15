from backend.tests import factories
from backend.tests.test_apis.test_dictionary_cleanup_api import TestDictionaryCleanupAPI


class TestDictionaryCleanupPreviewAPI(TestDictionaryCleanupAPI):
    API_LIST_VIEW = "api:dictionary-cleanup-preview-list"
    API_DETAIL_VIEW = "api:dictionary-cleanup-preview-detail"

    def create_minimal_instance(self, site, visibility):
        return factories.DictionaryCleanupJobFactory.create(site=site, is_preview=True)
