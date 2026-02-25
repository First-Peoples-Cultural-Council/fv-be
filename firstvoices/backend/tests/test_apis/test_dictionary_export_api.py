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
        part_of_speech = factories.PartOfSpeechFactory.create(title="PartOfSpeechTest")
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            title="Title",
            visibility=Visibility.PUBLIC,
            type=TypeOfDictionaryEntry.WORD,
            exclude_from_games=True,
            exclude_from_kids=True,
            part_of_speech=part_of_speech,
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
        assert first_row["part_of_speech"] == dictionary_entry.part_of_speech.title

    def test_array_fields(self, mock_search_query_execute):
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            translations=[
                "translation_1",
                "translation_2",
                "translation_3",
                "translation_4",
                "translation_5",
                "translation_6",
                "translation_7",
                "translation_8",
                "translation_9",
                "translation_10",
            ],
            notes=[
                "note_1",
                "note_2",
                "note_3",
                "note_4",
                "note_5",
                "note_6",
                "note_7",
                "note_8",
                "note_9",
                "note_10",
            ],
            acknowledgements=[
                "acknowledgement_1",
                "acknowledgement_2",
                "acknowledgement_3",
                "acknowledgement_4",
                "acknowledgement_5",
                "acknowledgement_6",
                "acknowledgement_7",
                "acknowledgement_8",
                "acknowledgement_9",
                "acknowledgement_10",
            ],
            pronunciations=[
                "pronunciation_1",
                "pronunciation_2",
                "pronunciation_3",
            ],
            alternate_spellings=[
                "alternate_spelling_1",
                "alternate_spelling_2",
                "alternate_spelling_3",
            ],
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(site_slug=self.site.slug), format="csv"
        )
        csv_rows = self.get_csv_rows(response)

        first_row = csv_rows[0]
        assert first_row["translation"] == dictionary_entry.translations[0]
        for i in range(2, 11):
            assert first_row[f"translation_{i}"] == dictionary_entry.translations[i - 1]

        assert first_row["note"] == dictionary_entry.notes[0]
        for i in range(2, 11):
            assert first_row[f"note_{i}"] == dictionary_entry.notes[i - 1]

        assert first_row["acknowledgement"] == dictionary_entry.acknowledgements[0]
        for i in range(2, 11):
            assert (
                first_row[f"acknowledgement_{i}"]
                == dictionary_entry.acknowledgements[i - 1]
            )

        assert first_row["pronunciation"] == dictionary_entry.pronunciations[0]
        assert first_row["pronunciation_2"] == dictionary_entry.pronunciations[1]
        assert first_row["pronunciation_3"] == dictionary_entry.pronunciations[2]

        assert (
            first_row["alternate_spelling"] == dictionary_entry.alternate_spellings[0]
        )
        assert (
            first_row["alternate_spelling_2"] == dictionary_entry.alternate_spellings[1]
        )
        assert (
            first_row["alternate_spelling_3"] == dictionary_entry.alternate_spellings[2]
        )

    def test_category_fields(self, mock_search_query_execute):
        category_1 = factories.CategoryFactory.create(title="Category1")
        category_2 = factories.CategoryFactory.create(title="Category2")
        category_3 = factories.CategoryFactory.create(title="Category3")
        category_4 = factories.CategoryFactory.create(title="Category4")
        category_5 = factories.CategoryFactory.create(title="Category5")
        category_6 = factories.CategoryFactory.create(title="Category6")
        category_7 = factories.CategoryFactory.create(title="Category7")
        category_8 = factories.CategoryFactory.create(title="Category8")
        category_9 = factories.CategoryFactory.create(title="Category9")
        category_10 = factories.CategoryFactory.create(title="Category10")

        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
        )
        dictionary_entry.categories.set(
            [
                category_1,
                category_2,
                category_3,
                category_4,
                category_5,
                category_6,
                category_7,
                category_8,
                category_9,
                category_10,
            ]
        )

        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(site_slug=self.site.slug), format="csv"
        )
        csv_rows = self.get_csv_rows(response)

        first_row = csv_rows[0]
        assert first_row["category"] == dictionary_entry.categories.first().title
        for i in range(2, 11):
            assert (
                first_row[f"category_{i}"]
                == dictionary_entry.categories.all()[i - 1].title
            )

    def test_media_fields(self, mock_search_query_execute):
        audio_1 = factories.AudioFactory.create(site=self.site)
        audio_2 = factories.AudioFactory.create(site=self.site)
        audio_3 = factories.AudioFactory.create(site=self.site)
        audio_4 = factories.AudioFactory.create(site=self.site)
        audio_5 = factories.AudioFactory.create(site=self.site)
        audio_6 = factories.AudioFactory.create(site=self.site)
        audio_7 = factories.AudioFactory.create(site=self.site)
        audio_8 = factories.AudioFactory.create(site=self.site)
        audio_9 = factories.AudioFactory.create(site=self.site)
        audio_10 = factories.AudioFactory.create(site=self.site)

        image_1 = factories.ImageFactory.create(site=self.site)
        image_2 = factories.ImageFactory.create(site=self.site)
        image_3 = factories.ImageFactory.create(site=self.site)
        image_4 = factories.ImageFactory.create(site=self.site)
        image_5 = factories.ImageFactory.create(site=self.site)
        image_6 = factories.ImageFactory.create(site=self.site)
        image_7 = factories.ImageFactory.create(site=self.site)
        image_8 = factories.ImageFactory.create(site=self.site)
        image_9 = factories.ImageFactory.create(site=self.site)
        image_10 = factories.ImageFactory.create(site=self.site)

        video_1 = factories.VideoFactory.create(site=self.site)
        video_2 = factories.VideoFactory.create(site=self.site)
        video_3 = factories.VideoFactory.create(site=self.site)
        video_4 = factories.VideoFactory.create(site=self.site)
        video_5 = factories.VideoFactory.create(site=self.site)
        video_6 = factories.VideoFactory.create(site=self.site)
        video_7 = factories.VideoFactory.create(site=self.site)
        video_8 = factories.VideoFactory.create(site=self.site)
        video_9 = factories.VideoFactory.create(site=self.site)
        video_10 = factories.VideoFactory.create(site=self.site)

        document_1 = factories.DocumentFactory.create(site=self.site)
        document_2 = factories.DocumentFactory.create(site=self.site)
        document_3 = factories.DocumentFactory.create(site=self.site)
        document_4 = factories.DocumentFactory.create(site=self.site)
        document_5 = factories.DocumentFactory.create(site=self.site)
        document_6 = factories.DocumentFactory.create(site=self.site)
        document_7 = factories.DocumentFactory.create(site=self.site)
        document_8 = factories.DocumentFactory.create(site=self.site)
        document_9 = factories.DocumentFactory.create(site=self.site)
        document_10 = factories.DocumentFactory.create(site=self.site)

        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            related_audio=[
                audio_1,
                audio_2,
                audio_3,
                audio_4,
                audio_5,
                audio_6,
                audio_7,
                audio_8,
                audio_9,
                audio_10,
            ],
            related_images=[
                image_1,
                image_2,
                image_3,
                image_4,
                image_5,
                image_6,
                image_7,
                image_8,
                image_9,
                image_10,
            ],
            related_videos=[
                video_1,
                video_2,
                video_3,
                video_4,
                video_5,
                video_6,
                video_7,
                video_8,
                video_9,
                video_10,
            ],
            related_documents=[
                document_1,
                document_2,
                document_3,
                document_4,
                document_5,
                document_6,
                document_7,
                document_8,
                document_9,
                document_10,
            ],
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

        audio_ids = [str(audio.id) for audio in dictionary_entry.related_audio.all()]
        for audio_id in audio_ids:
            assert audio_id in first_row["audio_ids"]

        image_ids = [str(image.id) for image in dictionary_entry.related_images.all()]
        for image_id in image_ids:
            assert image_id in first_row["img_ids"]

        video_ids = [str(video.id) for video in dictionary_entry.related_videos.all()]
        for video_id in video_ids:
            assert video_id in first_row["video_ids"]

        document_ids = [
            str(document.id) for document in dictionary_entry.related_documents.all()
        ]
        for document_id in document_ids:
            assert document_id in first_row["document_ids"]

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

    @pytest.mark.parametrize(
        "entry_type", [TypeOfDictionaryEntry.WORD, TypeOfDictionaryEntry.PHRASE]
    )
    def test_valid_types(self, entry_type, mock_search_query_execute):
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            title="Title",
            type=entry_type,
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(
                site_slug=self.site.slug, query_kwargs={"types": entry_type}
            ),
            format="csv",
        )
        csv_rows = self.get_csv_rows(response)

        first_row = csv_rows[0]
        assert first_row["id"] == str(dictionary_entry.id)

    @pytest.mark.parametrize("unsupported_type", ["invalid", "song", "story"])
    def test_unsupported_types_types(self, unsupported_type, mock_search_query_execute):
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            title="Title",
            type=TypeOfDictionaryEntry.WORD,
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(
                site_slug=self.site.slug, query_kwargs={"types": unsupported_type}
            ),
            format="csv",
        )

        assert response.status_code == 200
        csv_rows = self.get_csv_rows(response)
        assert len(csv_rows) == 0

    def test_page_size_cannot_exceed_limit(self, mock_search_query_execute):
        dictionary_entry = factories.DictionaryEntryFactory.create(
            site=self.site,
            title="Title",
            type=TypeOfDictionaryEntry.WORD,
        )
        self.mock_es_results(mock_search_query_execute, dictionary_entry.id)

        response = self.client.get(
            self.get_list_endpoint(
                site_slug=self.site.slug, query_kwargs={"pageSize": 5001}
            ),
            format="csv",
        )

        assert response.status_code == 400
        response_data = json.loads(response.content)
        assert (
            response_data[0]
            == "pageSize: The maximum number of entries per export is 5000."
        )
