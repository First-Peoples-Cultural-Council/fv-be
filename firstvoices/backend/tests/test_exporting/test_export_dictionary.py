import pytest

from backend.models import DictionaryEntry
from backend.resources.dictionary import DictionaryEntryResource
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentListEndpointMixin,
)


class TestExportDictionary(SiteContentListEndpointMixin, BaseSiteContentApiTest):
    API_LIST_VIEW = "api:dictionaryentry-list"

    def get_entry_as_csv_row(self, entry: DictionaryEntry):
        return (
            f"{str(entry.id)},{entry.title},{entry.type.label.lower()},{entry.visibility.label.lower()},"
            f"{self.get_all_cols(entry.translations)}"
        )

    def get_all_cols(self, related_list):
        all_cols = ["" for i in range(0, 5)]

        for i, item in enumerate(related_list):
            if i < len(all_cols):
                all_cols[i] = item

        return ",".join(all_cols)

    @pytest.mark.django_db
    def test_export_dictionary_csv_renderer(self):
        entry = factories.DictionaryEntryFactory.create()
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(entry.site.slug), HTTP_ACCEPT="text/csv"
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/csv; charset=utf-8"
        response_string = response.content.decode("utf-8")
        assert response_string.startswith(
            "id,title,type,visibility,"
            "translation,translation_2,translation_3,translation_4,translation_5,"
            "acknowledgement,"
            "alternate_spelling,exclude_from_games,exclude_from_kids,"
            "is_immersion_label,note,part_of_speech,pronunciation,site_slug,"
            "created,created_by,last_modified,last_modified_by\r\n"
        )

        assert self.get_entry_as_csv_row(entry) in response_string

    @pytest.mark.django_db
    def test_export_dictionary_resource(self):
        entry1 = factories.DictionaryEntryFactory.create()
        factories.DictionaryEntryFactory.create(site=entry1.site)
        factories.DictionaryEntryFactory.create()
        dataset = DictionaryEntryResource(site=entry1.site).export()
        assert len(dataset.dict) == 2
        assert dataset.csv.startswith(
            "id,created_by,created,last_modified_by,last_modified,site,visibility,include_in_games,"
            "include_on_kids_site,title,type,category,related_entry,related_characters,part_of_speech,note,"
            "acknowledgement,translation,alternate_spelling,pronunciation"
        )
