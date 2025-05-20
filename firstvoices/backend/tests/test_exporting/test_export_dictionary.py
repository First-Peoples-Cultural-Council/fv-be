import pytest

from backend.models import DictionaryEntry
from backend.tests import factories
from backend.tests.test_apis.base.base_uncontrolled_site_api import (
    BaseSiteContentApiTest,
    SiteContentListEndpointMixin,
)


class TestExportDictionary(SiteContentListEndpointMixin, BaseSiteContentApiTest):
    API_LIST_VIEW = "api:dictionaryentry-list"

    def get_csv_headers(self):
        h = (
            "id,title,type,visibility,"
            "alternate_spelling,alternate_spelling_2,alternate_spelling_3,alternate_spelling_4,alternate_spelling_5,"
            "translation,translation_2,translation_3,translation_4,translation_5,"
            "pronunciation,pronunciation_2,pronunciation_3,pronunciation_4,pronunciation_5,"
            "acknowledgement,acknowledgement_2,acknowledgement_3,acknowledgement_4,acknowledgement_5,"
            "note,note_2,note_3,note_4,note_5,"
            "exclude_from_games,exclude_from_kids,part_of_speech,"
            "audio_filename,audio_title,audio_description,audio_acknowledgement,audio_exclude_from_kids_site,"
            "audio_exclude_from_games,"
            "audio_speaker,audio_speaker_2,audio_speaker_3,audio_speaker_4,audio_speaker_5,"
            "audio_2_filename,audio_2_title,audio_2_description,audio_2_acknowledgement,"
            "audio_2_exclude_from_kids_site,audio_2_exclude_from_games,"
            "audio_2_speaker,audio_2_speaker_2,audio_2_speaker_3,audio_2_speaker_4,audio_2_speaker_5,"
            "audio_3_filename,audio_3_title,audio_3_description,audio_3_acknowledgement,"
            "audio_3_exclude_from_kids_site,audio_3_exclude_from_games,"
            "audio_3_speaker,audio_3_speaker_2,audio_3_speaker_3,audio_3_speaker_4,audio_3_speaker_5,"
            "audio_4_filename,audio_4_title,audio_4_description,audio_4_acknowledgement,"
            "audio_4_exclude_from_kids_site,audio_4_exclude_from_games,"
            "audio_4_speaker,audio_4_speaker_2,audio_4_speaker_3,audio_4_speaker_4,audio_4_speaker_5,"
            "audio_5_filename,audio_5_title,audio_5_description,audio_5_acknowledgement,"
            "audio_5_exclude_from_kids_site,audio_5_exclude_from_games,"
            "audio_5_speaker,audio_5_speaker_2,audio_5_speaker_3,audio_5_speaker_4,audio_5_speaker_5,"
            "img_filename,img_title,img_description,img_acknowledgement,img_exclude_from_kids_site,"
            "img_exclude_from_games,"
            "img_2_filename,img_2_title,img_2_description,img_2_acknowledgement,img_2_exclude_from_kids_site,"
            "img_2_exclude_from_games,"
            "img_3_filename,img_3_title,img_3_description,img_3_acknowledgement,img_3_exclude_from_kids_site,"
            "img_3_exclude_from_games,"
            "img_4_filename,img_4_title,img_4_description,img_4_acknowledgement,img_4_exclude_from_kids_site,"
            "img_4_exclude_from_games,"
            "img_5_filename,img_5_title,img_5_description,img_5_acknowledgement,img_5_exclude_from_kids_site,"
            "img_5_exclude_from_games,"
            "video_filename,video_title,video_description,video_acknowledgement,video_exclude_from_kids_site,"
            "video_exclude_from_games,"
            "video_2_filename,video_2_title,video_2_description,video_2_acknowledgement,"
            "video_2_exclude_from_kids_site,video_2_exclude_from_games,"
            "video_3_filename,video_3_title,video_3_description,video_3_acknowledgement,"
            "video_3_exclude_from_kids_site,video_3_exclude_from_games,"
            "video_4_filename,video_4_title,video_4_description,video_4_acknowledgement,"
            "video_4_exclude_from_kids_site,video_4_exclude_from_games,"
            "video_5_filename,video_5_title,video_5_description,video_5_acknowledgement,"
            "video_5_exclude_from_kids_site,video_5_exclude_from_games,"
            "site_slug,created,created_by,last_modified,last_modified_by"
        )
        return h

    def get_entry_as_csv_row(self, entry: DictionaryEntry):
        return (
            f"{str(entry.id)},{entry.title},{entry.type.label.lower()},{entry.visibility.label.lower()},"
            f"{self.get_all_cols(entry.alternate_spellings)}"
            f"{self.get_all_cols(entry.translations)}"
            f"{self.get_all_cols(entry.pronunciations)}"
            f"{self.get_all_cols(entry.acknowledgements)}"
            f"{self.get_all_cols(entry.notes)}"
            f"{entry.exclude_from_games},{entry.exclude_from_kids},{entry.part_of_speech},"
            f"{self.get_audio_url(entry.related_audio.first())}"
        )

    def get_all_cols(self, related_list):
        all_cols = ["" for i in range(0, 6)]

        for i, item in enumerate(related_list):
            if i < len(all_cols):
                all_cols[i] = item

        return ",".join(all_cols)

    def get_audio_url(self, audio):
        try:
            return f"http://testserver{audio.original.content.url}"
        except Exception:
            return ""

    @pytest.mark.django_db
    def test_export_dictionary_csv_renderer_has_correct_cols(self):
        entry = factories.DictionaryEntryFactory.create(
            translations=["translation 1", "translation 2", "translation 3"]
        )

        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(entry.site.slug), HTTP_ACCEPT="text/csv"
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/csv; charset=utf-8"
        response_string = response.content.decode("utf-8")
        assert response_string.startswith(self.get_csv_headers())

    @pytest.mark.django_db
    def test_export_dictionary_csv_renderer_has_correct_entries(self):
        entry = factories.DictionaryEntryFactory.create(
            translations=["translation 1", "translation 2", "translation 3"]
        )
        entry2 = factories.DictionaryEntryFactory.create(
            site=entry.site, translations=[]
        )
        entry3 = factories.DictionaryEntryFactory.create()

        audio = factories.AudioFactory.create(site=entry.site)
        speaker = factories.PersonFactory.create(site=entry.site)
        audio.speakers.add(speaker)
        speaker2 = factories.PersonFactory.create(site=entry.site)
        audio.speakers.add(speaker2)
        entry.related_audio.add(audio)

        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(entry.site.slug), HTTP_ACCEPT="text/csv"
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/csv; charset=utf-8"
        response_string = response.content.decode("utf-8")

        assert str(entry.id) in response_string
        assert str(entry2.id) in response_string
        assert str(entry3.id) not in response_string

    @pytest.mark.django_db
    def test_export_dictionary_csv_renderer_includes_related_values(self):
        entry = factories.DictionaryEntryFactory.create(
            translations=["translation 1", "translation 2", "translation 3"]
        )

        audio = factories.AudioFactory.create(site=entry.site)
        speaker = factories.PersonFactory.create(site=entry.site)
        audio.speakers.add(speaker)
        speaker2 = factories.PersonFactory.create(site=entry.site)
        audio.speakers.add(speaker2)
        entry.related_audio.add(audio)

        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(entry.site.slug), HTTP_ACCEPT="text/csv"
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/csv; charset=utf-8"
        response_string = response.content.decode("utf-8")

        assert self.get_entry_as_csv_row(entry) in response_string

    @pytest.mark.django_db
    def test_export_dictionary_csv_renderer_handles_blank_values(self):
        entry = factories.DictionaryEntryFactory.create(translations=[])

        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(entry.site.slug), HTTP_ACCEPT="text/csv"
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/csv; charset=utf-8"
        response_string = response.content.decode("utf-8")

        assert self.get_entry_as_csv_row(entry) in response_string

    @pytest.mark.django_db
    def test_export_dictionary_csv_renderer_handles_empty_list(self):
        site = factories.SiteFactory.create()
        user = factories.get_superadmin()
        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.get_list_endpoint(site.slug), HTTP_ACCEPT="text/csv"
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/csv; charset=utf-8"
        response_string = response.content.decode("utf-8")
        assert response_string.startswith(self.get_csv_headers())
