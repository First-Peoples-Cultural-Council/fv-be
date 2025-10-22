import csv
import io
import json
import re

import pytest

from backend.models.constants import AppRole, Role, Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentListEndpointMixin,
)
from backend.tests.test_apis.test_search_apis.base_search_test import SearchMocksMixin


@pytest.mark.django_db
class TestDictionaryExportAPI(
    SearchMocksMixin, SiteContentListEndpointMixin, BaseSiteContentApiTest
):
    API_LIST_VIEW = "api:dictionary-export-list"

    def setup_method(self):
        super().setup_method()
        self.site, self.user = factories.get_site_with_member(
            site_visibility=Visibility.PUBLIC, user_role=Role.LANGUAGE_ADMIN
        )
        self.client.force_authenticate(user=self.user)

    def mock_es_results(self, mock_search_query_execute, entry_id):
        mock_es_results = {
            "hits": {
                "hits": [
                    {
                        "_index": "dictionary_entries_2023_06_23_06_11_22",
                        "_id": str(entry_id),
                        "_score": 1.0,
                        "_source": {
                            "document_id": entry_id,
                            "document_type": "DictionaryEntry",
                            "site_id": self.site.id,
                        },
                    },
                ],
                "total": {"value": 1, "relation": "eq"},
            }
        }
        mock_search_query_execute.return_value = mock_es_results

    def get_csv_rows(self, response):
        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))

        rows = list(reader)
        assert len(rows) > 0

        headers = rows[0]
        csv_rows = [dict(zip(headers, row)) for row in rows[1:]]
        return csv_rows

    def test_filename(self, mock_search_query_execute):
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        assert "text/csv" in response["content-type"]

        file_header = response["content-disposition"]
        filename_pattern = rf"dictionary_export_{self.site.slug}_\d{{4}}_\d{{2}}_\d{{2}}_\d{{2}}_\d{{2}}_\d{{2}}"

        assert re.search(
            filename_pattern, file_header
        ), "Filename does match the expected format."

    def test_base_fields(self, mock_search_query_execute):
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            title="Title",
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            exclude_from_games=True,
            exclude_from_kids=True,
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(site_slug=self.site.slug), format="csv"
        )
        csv_rows = self.get_csv_rows(response)

        first_row = csv_rows[0]
        assert first_row["id"] == str(dictionary_entry.id)
        assert first_row["title"] == dictionary_entry.title
        assert first_row["type"] == dictionary_entry.type
        assert first_row["visibility"] == str(dictionary_entry.visibility.label).lower()
        assert first_row["type"] == str(dictionary_entry.type.label).lower()
        assert first_row["include_in_games"] == str(
            not dictionary_entry.exclude_from_games
        )
        assert first_row["include_on_kids_site"] == str(
            not dictionary_entry.exclude_from_kids
        )

    def test_array_fields(self, mock_search_query_execute):
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            translations=["translation_1", "translation_2"],
            notes=["note_1", "note_2"],
            pronunciations=["pronunciation_1", "pronunciation_2"],
            acknowledgements=["acknowledgement_1", "acknowledgement_2"],
            alternate_spellings=["alternate_spelling_1", "alternate_spelling_2"],
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(site_slug=self.site.slug), format="csv"
        )
        csv_rows = self.get_csv_rows(response)

        first_row = csv_rows[0]
        assert first_row["translation"] == dictionary_entry.translations[0]
        assert first_row["translation_2"] == dictionary_entry.translations[1]
        assert first_row["note"] == dictionary_entry.notes[0]
        assert first_row["note_2"] == dictionary_entry.notes[1]
        assert first_row["pronunciation"] == dictionary_entry.pronunciations[0]
        assert first_row["pronunciation_2"] == dictionary_entry.pronunciations[1]
        assert first_row["acknowledgement"] == dictionary_entry.acknowledgements[0]
        assert first_row["acknowledgement_2"] == dictionary_entry.acknowledgements[1]
        assert (
            first_row["alternate_spelling"] == dictionary_entry.alternate_spellings[0]
        )
        assert (
            first_row["alternate_spelling_2"] == dictionary_entry.alternate_spellings[1]
        )

    def test_media_fields(self, mock_search_query_execute):
        audio_1 = factories.AudioFactory.create(site=self.site)
        audio_2 = factories.AudioFactory.create(site=self.site)
        image_1 = factories.ImageFactory.create(site=self.site)
        image_2 = factories.ImageFactory.create(site=self.site)
        video_1 = factories.VideoFactory.create(site=self.site)
        video_2 = factories.VideoFactory.create(site=self.site)
        document_1 = factories.DocumentFactory.create(site=self.site)
        document_2 = factories.DocumentFactory.create(site=self.site)

        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            related_audio=[audio_1, audio_2],
            related_images=[image_1, image_2],
            related_videos=[video_1, video_2],
            related_documents=[document_1, document_2],
            related_video_links=[
                "https://www.youtube.com/watch?v=abc123",
                "https://www.youtube.com/watch?v=xyz456",
            ],
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(site_slug=self.site.slug), format="csv"
        )
        csv_rows = self.get_csv_rows(response)

        first_row = csv_rows[0]
        assert dictionary_entry.related_video_links[0] in first_row["video_embed_links"]
        assert dictionary_entry.related_video_links[1] in first_row["video_embed_links"]

        assert str(audio_1.id) in first_row["audio_ids"]
        assert str(audio_2.id) in first_row["audio_ids"]
        assert str(image_1.id) in first_row["img_ids"]
        assert str(image_2.id) in first_row["img_ids"]
        assert str(video_1.id) in first_row["video_ids"]
        assert str(video_2.id) in first_row["video_ids"]
        assert str(document_1.id) in first_row["document_ids"]
        assert str(document_2.id) in first_row["document_ids"]

    def test_external_system(self, mock_search_query_execute):
        external_system = factories.ExternalDictionaryEntrySystemFactory.create()
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            external_system=external_system,
        )

        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(site_slug=self.site.slug), format="csv"
        )
        csv_rows = self.get_csv_rows(response)
        first_row = csv_rows[0]
        assert first_row["external_system"] == external_system.title

    def test_empty_results(self, mock_search_query_execute):
        # Emulating a search query which doesn't returns any hits on dictionary entries
        mock_es_results = {
            "hits": {
                "hits": [],
                "total": {"value": 0, "relation": "eq"},
            }
        }
        mock_search_query_execute.return_value = mock_es_results
        response = self.client.get(
            self.get_list_endpoint(site_slug=self.site.slug), format="csv"
        )
        csv_rows = self.get_csv_rows(response)

        assert len(csv_rows) == 0

    # Test permissions
    # Only language admins, staff and super admins should be able to export
    @pytest.mark.parametrize("role", [AppRole.STAFF, AppRole.SUPERADMIN])
    def test_superadmins_have_access(self, role, mock_search_query_execute):
        if role == AppRole.SUPERADMIN:
            self.site, self.user = factories.get_site_with_app_admin(self.client)
        elif role == AppRole.STAFF:
            self.site, self.user = factories.get_site_with_staff_user(self.client)

        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        assert "text/csv" in response["content-type"]

    def test_language_admins_have_access(self, mock_search_query_execute):
        self.site, self.user = factories.get_site_with_authenticated_member(
            self.client, Visibility.TEAM, Role.LANGUAGE_ADMIN
        )
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(self.get_list_endpoint(site_slug=self.site.slug))

        assert response.status_code == 200
        assert "text/csv" in response["content-type"]

    @pytest.mark.parametrize("role", [Role.MEMBER, Role.EDITOR, Role.ASSISTANT])
    def test_non_language_admins_have_no_access(self, role, mock_search_query_execute):
        self.site, self.user = factories.get_site_with_authenticated_member(
            self.client, Visibility.PUBLIC, role
        )

        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
        )

        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(site_slug=self.site.slug), format="csv"
        )
        assert response.status_code == 403
        response_data = json.loads(response.content)

        assert (
            response_data["detail"]
            == "You do not have permission to perform this action."
        )

    @pytest.mark.parametrize(
        "site_visibility", [Visibility.PUBLIC, Visibility.TEAM, Visibility.MEMBERS]
    )
    def test_unauthorized_users_have_no_access(
        self, site_visibility, mock_search_query_execute
    ):
        self.site, self.user = factories.get_site_with_authenticated_nonmember(
            self.client, visibility=site_visibility
        )

        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
        )

        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(site_slug=self.site.slug), format="csv"
        )
        assert response.status_code == 403
        response_data = json.loads(response.content)

        assert (
            response_data["detail"]
            == "You do not have permission to perform this action."
        )
