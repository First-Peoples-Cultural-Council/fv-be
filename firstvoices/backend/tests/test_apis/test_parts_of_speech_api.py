from rest_framework.test import APIClient

from backend.models import PartOfSpeech
from backend.tests import factories
from backend.tests.test_apis.base.base_non_site_api import ReadOnlyNonSiteApiTest


class TestPartsOfSpeechAPI(ReadOnlyNonSiteApiTest):
    """Tests for parts-of-speech views."""

    FIXTURE_FILE = "partsOfSpeech_initial.json"
    API_LIST_VIEW = "api:partofspeech-list"
    API_DETAIL_VIEW = "api:partofspeech-detail"

    def setup_method(self):
        self.client = APIClient()

        # delete parts of speech that are loaded from a fixture, so we can test our standard list cases
        children = PartOfSpeech.objects.all().exclude(parent__isnull=True)
        for c in children:
            c.delete()

        parents = PartOfSpeech.objects.all().filter()
        for p in parents:
            p.delete()

    def create_minimal_instance(self, visibility):
        return factories.PartOfSpeechFactory.create()

    def get_expected_response(self, instance):
        return {
            "id": str(instance.id),
            "title": instance.title,
            "parent": self.get_expected_parent_response(instance),
        }

    def get_expected_parent_response(self, instance):
        try:
            return {
                "id": str(instance.parent.id),
                "title": instance.parent.title,
            }
        except AttributeError:
            return None
