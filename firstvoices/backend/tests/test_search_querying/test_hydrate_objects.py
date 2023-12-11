import uuid

import pytest

from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.search.utils.hydration_utils import hydrate_objects
from backend.tests import factories
from backend.tests.factories import (
    AudioFactory,
    AudioSpeakerFactory,
    DictionaryEntryFactory,
    ImageFactory,
    ImageFileFactory,
    PersonFactory,
    SiteFactory,
    SongFactory,
    StoryFactory,
    TranslationFactory,
    VideoFactory,
)


def assert_site_object(hydrated_object_entry, site_instance):
    assert hydrated_object_entry["site"]["id"] == str(site_instance.id)
    assert hydrated_object_entry["site"]["slug"] == site_instance.slug
    assert hydrated_object_entry["site"]["title"] == site_instance.title
    assert (
        hydrated_object_entry["site"]["visibility"]
        == site_instance.get_visibility_display().lower()
    )


def assert_related_audio(hydrated_object_entry, audio_instance, speaker):
    assert hydrated_object_entry["related_audio"][0]["id"] == str(audio_instance.id)
    assert hydrated_object_entry["related_audio"][0]["title"] == audio_instance.title
    assert (
        hydrated_object_entry["related_audio"][0]["description"]
        == audio_instance.description
    )
    assert (
        hydrated_object_entry["related_audio"][0]["acknowledgement"]
        == audio_instance.acknowledgement
    )
    # speakers
    assert hydrated_object_entry["related_audio"][0]["speakers"][0]["id"] == str(
        speaker.id
    )
    assert (
        hydrated_object_entry["related_audio"][0]["speakers"][0]["name"] == speaker.name
    )
    assert (
        hydrated_object_entry["related_audio"][0]["speakers"][0]["bio"] == speaker.bio
    )
    # original
    assert (
        hydrated_object_entry["related_audio"][0]["original"]["path"]
        == audio_instance.original.content.url
    )
    assert (
        hydrated_object_entry["related_audio"][0]["original"]["mimetype"]
        == audio_instance.original.mimetype
    )
    assert (
        hydrated_object_entry["related_audio"][0]["original"]["size"]
        == audio_instance.original.size
    )


def assert_related_images(hydrated_object_entry, image_instance):
    assert hydrated_object_entry["related_images"][0]["id"] == str(image_instance.id)
    assert (
        hydrated_object_entry["related_images"][0]["original"]["path"]
        == image_instance.original.content.url
    )
    assert (
        hydrated_object_entry["related_images"][0]["original"]["mimetype"]
        == image_instance.original.mimetype
    )
    assert (
        hydrated_object_entry["related_images"][0]["original"]["size"]
        == image_instance.original.size
    )
    assert (
        hydrated_object_entry["related_images"][0]["original"]["height"]
        == image_instance.original.height
    )
    assert (
        hydrated_object_entry["related_images"][0]["original"]["width"]
        == image_instance.original.width
    )


def assert_related_videos(hydrated_object_entry, video_instance):
    assert hydrated_object_entry["related_videos"][0]["id"] == str(video_instance.id)
    assert (
        hydrated_object_entry["related_videos"][0]["original"]["path"]
        == video_instance.original.content.url
    )
    assert (
        hydrated_object_entry["related_videos"][0]["original"]["mimetype"]
        == video_instance.original.mimetype
    )
    assert (
        hydrated_object_entry["related_videos"][0]["original"]["size"]
        == video_instance.original.size
    )
    assert (
        hydrated_object_entry["related_images"][0]["original"]["height"]
        == video_instance.original.height
    )
    assert (
        hydrated_object_entry["related_images"][0]["original"]["width"]
        == video_instance.original.width
    )


def assert_translations(hydrated_object_entry, translation):
    assert hydrated_object_entry["translations"][0]["id"] == str(translation.id)
    assert hydrated_object_entry["translations"][0]["text"] == translation.text


@pytest.mark.django_db
class TestHydrateObjects:
    def test_hydrate_exception_case(self, caplog):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        invalid_uuid = uuid.uuid4()
        search_result_with_invalid_id = {
            "_index": "dictionary_entries_2023_11_01_21_32_51",
            "_id": "searchId123",
            "_score": 1.0,
            "_source": {
                "document_id": invalid_uuid,
                "site_id": site.id,
            },
        }

        hydrate_objects([search_result_with_invalid_id])
        assert f"Object not found in database with id: {invalid_uuid}" in caplog.text

    @pytest.mark.parametrize(
        "entry_type", [TypeOfDictionaryEntry.WORD, TypeOfDictionaryEntry.PHRASE]
    )
    def test_dictionary_entry_hydration(self, entry_type):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        entry = DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC, type=entry_type
        )

        translation = TranslationFactory.create(
            dictionary_entry=entry, text="translation"
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
        assert actual_hydrated_object["type"] == entry_type.label.lower()

        # entry
        assert hydrated_object_entry["id"] == str(entry.id)
        assert hydrated_object_entry["title"] == entry.title
        assert hydrated_object_entry["type"] == entry.type
        assert (
            hydrated_object_entry["visibility"]
            == entry.get_visibility_display().lower()
        )

        assert_site_object(hydrated_object_entry, site)
        assert_translations(hydrated_object_entry, translation)
        assert_related_audio(hydrated_object_entry, audio, speaker)
        assert_related_images(hydrated_object_entry, image)

    @pytest.mark.parametrize(
        "entry_type",
        [TypeOfDictionaryEntry.WORD, TypeOfDictionaryEntry.PHRASE],
    )
    @pytest.mark.parametrize(
        "games_flag, should_have_split_chars_base",
        [
            (True, True),
            (False, False),
            (None, False),
        ],
    )
    def test_dictionary_entry_games_hydration(
        self, entry_type, games_flag, should_have_split_chars_base
    ):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        factories.CharacterFactory.create(title="üü", site=site)
        factories.CharacterFactory.create(title="a", site=site)
        entry = DictionaryEntryFactory.create(
            site=site, visibility=Visibility.PUBLIC, type=entry_type, title="aüüa"
        )

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
        actual_hydrated_object = hydrate_objects(
            [minimal_dictionary_search_result], games_flag=games_flag
        )[0]
        hydrated_object_entry = actual_hydrated_object["entry"]

        assert (
            actual_hydrated_object["searchResultId"]
            == minimal_dictionary_search_result["_id"]
        )
        assert actual_hydrated_object["type"] == entry_type.label.lower()

        # entry
        assert hydrated_object_entry["id"] == str(entry.id)
        assert hydrated_object_entry["title"] == entry.title
        assert hydrated_object_entry["type"] == entry.type
        assert (
            hydrated_object_entry["visibility"]
            == entry.get_visibility_display().lower()
        )

        assert_site_object(hydrated_object_entry, site)

        if should_have_split_chars_base:
            assert "split_chars_base" in hydrated_object_entry
            assert hydrated_object_entry["split_chars_base"] == ["a", "üü", "a"]
        else:
            assert "split_chars_base" not in hydrated_object_entry

    def test_song_hydration(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        image = ImageFactory.create(site=site)
        video = VideoFactory.create(site=site)
        song = SongFactory.create(
            site=site,
            hide_overlay=True,
            related_images=(image,),
            related_videos=(video,),
        )

        # Only adding the fields required for hydrate_objects method to work,
        # the rest should be fetched from the db
        minimal_song_search_result = {
            "_index": "songs_2023_11_01_21_32_51",
            "_id": "searchId123",
            "_score": 1.0,
            "_source": {
                "document_id": song.id,
                "site_id": site.id,
            },
        }

        actual_hydrated_object = hydrate_objects([minimal_song_search_result])[0]
        hydrated_object_entry = actual_hydrated_object["entry"]

        assert (
            actual_hydrated_object["searchResultId"]
            == minimal_song_search_result["_id"]
        )
        assert actual_hydrated_object["type"] == "song"

        # entry
        assert hydrated_object_entry["id"] == str(song.id)
        assert hydrated_object_entry["title"] == song.title
        assert hydrated_object_entry["title_translation"] == song.title_translation
        assert hydrated_object_entry["hide_overlay"] == song.hide_overlay
        assert (
            hydrated_object_entry["visibility"] == song.get_visibility_display().lower()
        )

        assert_site_object(hydrated_object_entry, site)
        assert_related_images(hydrated_object_entry, image)
        assert_related_videos(hydrated_object_entry, video)

    def test_story_hydration(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        image = ImageFactory.create(site=site)
        video = VideoFactory.create(site=site)
        story = StoryFactory.create(
            site=site,
            hide_overlay=True,
            related_images=(image,),
            related_videos=(video,),
        )

        # Only adding the fields required for hydrate_objects method to work,
        # the rest should be fetched from the db
        minimal_story_search_result = {
            "_index": "stories_2023_11_01_21_32_51",
            "_id": "searchId123",
            "_score": 1.0,
            "_source": {
                "document_id": story.id,
                "site_id": site.id,
            },
        }

        actual_hydrated_object = hydrate_objects([minimal_story_search_result])[0]
        hydrated_object_entry = actual_hydrated_object["entry"]

        assert (
            actual_hydrated_object["searchResultId"]
            == minimal_story_search_result["_id"]
        )
        assert actual_hydrated_object["type"] == "story"

        # entry
        assert hydrated_object_entry["id"] == str(story.id)
        assert hydrated_object_entry["title"] == story.title
        assert hydrated_object_entry["title_translation"] == story.title_translation
        assert hydrated_object_entry["hide_overlay"] == story.hide_overlay
        assert hydrated_object_entry["author"] == story.author
        assert (
            hydrated_object_entry["visibility"]
            == story.get_visibility_display().lower()
        )

        assert_site_object(hydrated_object_entry, site)
        assert_related_images(hydrated_object_entry, image)
        assert_related_videos(hydrated_object_entry, video)

    def test_audio_hydration(self):
        site = SiteFactory(visibility=Visibility.PUBLIC)

        speaker = PersonFactory.create(site=site)
        audio = AudioFactory.create(
            site=site, acknowledgement="ack ack", description="audio file"
        )
        AudioSpeakerFactory.create(speaker=speaker, audio=audio)

        # Only adding the fields required for hydrate_objects method to work,
        # the rest should be fetched from the db
        minimal_audio_search_result = {
            "_index": "media_2023_11_01_21_32_51",
            "_id": "searchId123",
            "_score": 1.0,
            "_source": {
                "document_id": audio.id,
                "site_id": site.id,
                "type": "audio",
            },
        }

        # Verifying the structure for only one word with all fields present
        actual_hydrated_object = hydrate_objects([minimal_audio_search_result])[0]
        hydrated_object_entry = actual_hydrated_object["entry"]

        assert (
            actual_hydrated_object["searchResultId"]
            == minimal_audio_search_result["_id"]
        )
        assert actual_hydrated_object["type"] == "audio"

        # entry
        assert hydrated_object_entry["id"] == str(audio.id)
        assert hydrated_object_entry["title"] == audio.title
        assert hydrated_object_entry["description"] == audio.description
        assert hydrated_object_entry["acknowledgement"] == audio.acknowledgement

        # original
        assert hydrated_object_entry["original"]["path"] == audio.original.content.url
        assert hydrated_object_entry["original"]["mimetype"] == audio.original.mimetype
        assert hydrated_object_entry["original"]["size"] == audio.original.size

        # speakers
        assert hydrated_object_entry["speakers"][0]["id"] == str(speaker.id)
        assert hydrated_object_entry["speakers"][0]["name"] == speaker.name
        assert hydrated_object_entry["speakers"][0]["bio"] == speaker.bio

    @pytest.mark.parametrize("media_type", ["image", "video"])
    def test_image_video_hydration(self, media_type):
        site = SiteFactory(visibility=Visibility.PUBLIC)
        small = ImageFileFactory.create(site=site)

        if media_type == "video":
            entry = VideoFactory.create(site=site, description="test desc", small=small)
        else:
            entry = ImageFactory.create(site=site, description="test desc", small=small)

        # Only adding the fields required for hydrate_objects method to work,
        # the rest should be fetched from the db
        minimal_audio_search_result = {
            "_index": "media_2023_11_01_21_32_51",
            "_id": "searchId123",
            "_score": 1.0,
            "_source": {
                "document_id": entry.id,
                "site_id": site.id,
                "type": media_type,
            },
        }

        # Verifying the structure for only one word with all fields present
        actual_hydrated_object = hydrate_objects([minimal_audio_search_result])[0]
        hydrated_object_entry = actual_hydrated_object["entry"]

        assert (
            actual_hydrated_object["searchResultId"]
            == minimal_audio_search_result["_id"]
        )
        assert actual_hydrated_object["type"] == media_type

        # entry
        assert hydrated_object_entry["id"] == str(entry.id)
        assert hydrated_object_entry["title"] == entry.title
        assert hydrated_object_entry["description"] == entry.description

        # original
        assert hydrated_object_entry["original"]["path"] == entry.original.content.url
        assert hydrated_object_entry["original"]["mimetype"] == entry.original.mimetype
        assert hydrated_object_entry["original"]["size"] == entry.original.size
        assert hydrated_object_entry["original"]["height"] == entry.original.height
        assert hydrated_object_entry["original"]["width"] == entry.original.width

        # small
        assert hydrated_object_entry["small"]["path"] == entry.small.content.url
