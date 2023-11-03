import pytest

from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.search.utils.constants import (
    ELASTICSEARCH_DICTIONARY_ENTRY_INDEX,
    ELASTICSEARCH_MEDIA_INDEX,
    ELASTICSEARCH_SONG_INDEX,
    ELASTICSEARCH_STORY_INDEX,
)
from backend.search.utils.hydration_utils import (
    handle_hydration_errors,
    hydrate_objects,
    separate_object_ids,
)
from backend.tests.factories import (
    AudioFactory,
    AudioSpeakerFactory,
    DictionaryEntryFactory,
    ImageFactory,
    PersonFactory,
    SiteFactory,
    TranslationFactory,
)


class TestSeparateObjectIds:
    TEST_DICTIONARY_ENTRY_INDEX_NAME = "dictionary_entries_2023_10_18_21_45_08"
    TEST_SONGS_INDEX_NAME = "songs_2023_10_18_21_45_08"
    TEST_STORIES_INDEX_NAME = "stories_2023_10_18_21_45_08"
    TEST_MEDIA_INDEX_NAME = "media_2023_10_18_21_45_09"

    def test_basic_separation(self):
        search_results = [
            {
                "_index": self.TEST_DICTIONARY_ENTRY_INDEX_NAME,
                "_source": {"document_id": 1},
            },
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 2}},
            {"_index": self.TEST_STORIES_INDEX_NAME, "_source": {"document_id": 3}},
            {
                "_index": self.TEST_MEDIA_INDEX_NAME,
                "_source": {"document_id": 4, "type": "audio"},
            },
        ]
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [1],
            ELASTICSEARCH_SONG_INDEX: [2],
            ELASTICSEARCH_STORY_INDEX: [3],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [4], "image": [], "video": []},
        }
        assert separate_object_ids(search_results) == expected_output

    def test_different_data_types(self):
        search_results = [
            {
                "_index": self.TEST_MEDIA_INDEX_NAME,
                "_source": {"document_id": 4, "type": "image"},
            },
            {
                "_index": self.TEST_MEDIA_INDEX_NAME,
                "_source": {"document_id": 5, "type": "video"},
            },
            {
                "_index": self.TEST_MEDIA_INDEX_NAME,
                "_source": {"document_id": 6, "type": "audio"},
            },
        ]
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [],
            ELASTICSEARCH_SONG_INDEX: [],
            ELASTICSEARCH_STORY_INDEX: [],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [6], "image": [4], "video": [5]},
        }
        assert separate_object_ids(search_results) == expected_output

    def test_multiple_objects_from_same_index(self):
        search_results = [
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 13}},
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 14}},
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 15}},
        ]
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [],
            ELASTICSEARCH_SONG_INDEX: [13, 14, 15],
            ELASTICSEARCH_STORY_INDEX: [],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [], "image": [], "video": []},
        }
        assert separate_object_ids(search_results) == expected_output

    def test_unknown_index(self):
        search_results = [
            {"_index": "unknown_index", "_source": {"document_id": 7}},
            {"_index": self.TEST_SONGS_INDEX_NAME, "_source": {"document_id": 8}},
        ]
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [],
            ELASTICSEARCH_SONG_INDEX: [8],
            ELASTICSEARCH_STORY_INDEX: [],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [], "image": [], "video": []},
        }
        assert separate_object_ids(search_results) == expected_output

    def test_empty_input(self):
        search_results = []
        expected_output = {
            ELASTICSEARCH_DICTIONARY_ENTRY_INDEX: [],
            ELASTICSEARCH_SONG_INDEX: [],
            ELASTICSEARCH_STORY_INDEX: [],
            ELASTICSEARCH_MEDIA_INDEX: {"audio": [], "image": [], "video": []},
        }
        assert separate_object_ids(search_results) == expected_output


class TestHandleHydrationErrors:
    doc_id = 123
    minimal_obj = {"_source": {"document_id": doc_id}}

    def test_object_not_found_in_db(self, caplog):
        exception = KeyError(f"Object not found in db. id: {self.doc_id}")
        handle_hydration_errors(self.minimal_obj, exception)
        assert f"Object not found in database with id: {self.doc_id}" in caplog.text

    def test_general_exception(self, caplog):
        exception = Exception("Random exception")
        handle_hydration_errors(self.minimal_obj, exception)
        expected_error_message = f"Error during hydration process. Document id: {self.doc_id}. Error: Random exception"
        assert expected_error_message in caplog.text


@pytest.mark.django_db
class TestHydrateObjects:
    def test_dictionary_entries_hydration(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        entry = DictionaryEntryFactory.create(site=site, visibility=Visibility.PUBLIC)

        translation_1 = TranslationFactory.create(
            dictionary_entry=entry, text="translation_1"
        )
        translation_2 = TranslationFactory.create(
            dictionary_entry=entry, text="translation_2"
        )

        audio = AudioFactory.create(site=site)
        entry.related_audio.add(audio)
        speaker = PersonFactory.create(site=site, bio="bio")
        AudioSpeakerFactory.create(audio=audio, speaker=speaker)

        image = ImageFactory.create(site=site)
        entry.related_images.add(image)

        # Only adding the fields required for hydarate_objects method to work,
        # the rest should be fetched from the db
        minimal_dictionary_search_result = {
            "_index": "dictionary_entries_2023_11_01_21_32_51",
            "_id": "searchId123",
            "_score": 1.0,
            "_source": {
                "document_id": entry.id,
                "site_id": site.id,
            },
        }

        # Verifying the structure for only one word with all fields present
        actual_hydrated_object = hydrate_objects([minimal_dictionary_search_result])[0]
        hydrated_object_entry = actual_hydrated_object["entry"]

        assert (
            actual_hydrated_object["searchResultId"]
            == minimal_dictionary_search_result["_id"]
        )
        assert (
            actual_hydrated_object["type"] == TypeOfDictionaryEntry.WORD.label.lower()
        )

        # entry
        assert hydrated_object_entry["id"] == str(entry.id)
        assert hydrated_object_entry["title"] == entry.title
        assert hydrated_object_entry["type"] == entry.type
        assert (
            hydrated_object_entry["visibility"]
            == entry.get_visibility_display().lower()
        )

        # Site
        assert hydrated_object_entry["site"]["id"] == str(site.id)
        assert hydrated_object_entry["site"]["slug"] == site.slug
        assert hydrated_object_entry["site"]["title"] == site.title
        assert (
            hydrated_object_entry["site"]["visibility"]
            == site.get_visibility_display().lower()
        )

        # Translations
        assert hydrated_object_entry["translations"][0]["id"] == str(translation_1.id)
        assert hydrated_object_entry["translations"][0]["text"] == translation_1.text
        assert hydrated_object_entry["translations"][1]["id"] == str(translation_2.id)
        assert hydrated_object_entry["translations"][1]["text"] == translation_2.text

        # Related audio
        assert hydrated_object_entry["related_audio"][0]["id"] == str(audio.id)
        assert hydrated_object_entry["related_audio"][0]["title"] == audio.title
        assert (
            hydrated_object_entry["related_audio"][0]["description"]
            == audio.description
        )
        assert (
            hydrated_object_entry["related_audio"][0]["acknowledgement"]
            == audio.acknowledgement
        )
        # speakers
        assert hydrated_object_entry["related_audio"][0]["speakers"][0]["id"] == str(
            speaker.id
        )
        assert (
            hydrated_object_entry["related_audio"][0]["speakers"][0]["name"]
            == speaker.name
        )
        assert (
            hydrated_object_entry["related_audio"][0]["speakers"][0]["bio"]
            == speaker.bio
        )
        # original
        assert (
            hydrated_object_entry["related_audio"][0]["original"]["path"]
            == audio.original.content.url
        )
        assert (
            hydrated_object_entry["related_audio"][0]["original"]["mimetype"]
            == audio.original.mimetype
        )
        assert (
            hydrated_object_entry["related_audio"][0]["original"]["size"]
            == audio.original.size
        )

        # related images
        assert hydrated_object_entry["related_images"][0]["id"] == str(image.id)
        assert (
            hydrated_object_entry["related_images"][0]["original"]["path"]
            == image.original.content.url
        )
        assert (
            hydrated_object_entry["related_images"][0]["original"]["mimetype"]
            == image.original.mimetype
        )
        assert (
            hydrated_object_entry["related_images"][0]["original"]["size"]
            == image.original.size
        )
        assert (
            hydrated_object_entry["related_images"][0]["original"]["height"]
            == image.original.height
        )
        assert (
            hydrated_object_entry["related_images"][0]["original"]["width"]
            == image.original.width
        )
