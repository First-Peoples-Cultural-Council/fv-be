from unittest.mock import patch

import pytest
from django.core.management import call_command

from backend.models.category import Category
from backend.models.characters import (
    Alphabet,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from backend.models.constants import AppRole
from backend.models.dictionary import DictionaryEntry
from backend.models.galleries import Gallery
from backend.models.immersion_labels import ImmersionLabel
from backend.models.media import Audio, Image, Person, Video
from backend.models.sites import Site, SiteFeature
from backend.models.song import Song
from backend.models.story import Story
from backend.tests.factories import (
    AlphabetFactory,
    AudioFactory,
    AudioSpeakerFactory,
    CharacterFactory,
    CharacterVariantFactory,
    ChildCategoryFactory,
    DictionaryEntryFactory,
    GalleryFactory,
    GalleryItemFactory,
    IgnoredCharacterFactory,
    ImageFactory,
    ImmersionLabelFactory,
    ImportJobFactory,
    LyricsFactory,
    ParentCategoryFactory,
    PersonFactory,
    SiteFactory,
    SiteFeatureFactory,
    SongFactory,
    StoryFactory,
    StoryPageFactory,
    VideoFactory,
    get_app_admin,
)


@pytest.mark.django_db
class TestCopySite:
    SOURCE_SLUG = "source"
    TARGET_SLUG = "target"

    def setup_method(self):
        self.source_site = SiteFactory.create(slug=self.SOURCE_SLUG, title="source")
        self.superadmin_user = get_app_admin(AppRole.SUPERADMIN)

    def call_copy_site_command(self):
        # helper function
        call_command(
            "copy_site",
            source_slug=self.SOURCE_SLUG,
            target_slug=self.TARGET_SLUG,
            email=self.superadmin_user.email,
        )

    def test_missing_source_site_raises_error(self):
        with pytest.raises(AttributeError) as e:
            call_command(
                "copy_site",
                source_slug="does_not_exist",
                target_slug=self.TARGET_SLUG,
                email=self.superadmin_user.email,
            )
        assert str(e.value) == "Provided source site does not exist."

    def test_force_delete_flag(self):
        old_target_site = SiteFactory.create(slug=self.TARGET_SLUG)
        old_site_created_timestamp = old_target_site.created

        call_command(
            "copy_site",
            source_slug=self.SOURCE_SLUG,
            target_slug=self.TARGET_SLUG,
            email=self.superadmin_user.email,
            force_delete=True,
        )

        new_target_site = Site.objects.get(slug=self.TARGET_SLUG)
        assert new_target_site.created != old_site_created_timestamp

    def test_existing_target_site_raises_error(self):
        SiteFactory.create(slug=self.TARGET_SLUG)
        with pytest.raises(AttributeError) as e:
            self.call_copy_site_command()
        assert (
            str(e.value)
            == f"Site with slug {self.TARGET_SLUG} already exists. Use --force-delete to override."
        )

    def test_invalid_target_user_raises_error(self):
        with pytest.raises(AttributeError) as e:
            call_command(
                "copy_site",
                source_slug=self.SOURCE_SLUG,
                target_slug=self.TARGET_SLUG,
                email="notareal@email.com",
            )
        assert str(e.value) == "No user found with the provided email."

    def test_site_attributes(self):
        self.call_copy_site_command()

        source_site = Site.objects.get(slug=self.SOURCE_SLUG)
        target_site = Site.objects.get(slug=self.TARGET_SLUG)

        assert target_site.title == self.TARGET_SLUG
        assert target_site.language == source_site.language
        assert target_site.visibility == source_site.visibility
        assert target_site.is_hidden == source_site.is_hidden
        assert target_site.contact_email_old is None
        assert len(target_site.contact_emails) == 0
        assert target_site.homepage is None
        assert target_site.logo is None
        assert target_site.banner_image is None
        assert target_site.banner_video is None

        assert target_site.created_by.email == self.superadmin_user.email
        assert target_site.last_modified_by.email == self.superadmin_user.email

    def test_site_features(self):
        source_feature_enabled = SiteFeatureFactory.create(
            site=self.source_site, key="first_feature", is_enabled=True
        )
        source_feature_disabled = SiteFeatureFactory.create(
            site=self.source_site, key="second_feature", is_enabled=False
        )

        self.call_copy_site_command()

        target_feature_enabled = SiteFeature.objects.get(
            site__slug=self.TARGET_SLUG, key="first_feature"
        )
        target_feature_disabled = SiteFeature.objects.get(
            site__slug=self.TARGET_SLUG, key="second_feature"
        )

        assert target_feature_enabled.is_enabled == source_feature_enabled.is_enabled
        assert target_feature_disabled.is_enabled == source_feature_disabled.is_enabled

    def test_characters_and_variants(self):
        source_img_1 = ImageFactory(site=self.source_site)
        source_img_2 = ImageFactory(site=self.source_site)
        source_video_1 = VideoFactory(site=self.source_site)
        source_video_2 = VideoFactory(site=self.source_site)
        source_audio_1 = AudioFactory(site=self.source_site)
        source_audio_2 = AudioFactory(site=self.source_site)

        source_char = CharacterFactory(site=self.source_site)
        source_char_variant = CharacterVariantFactory(
            site=self.source_site, base_character=source_char
        )

        source_char.related_images.set([source_img_1, source_img_2])
        source_char.related_videos.set([source_video_1, source_video_2])
        source_char.related_audio.set([source_audio_1, source_audio_2])
        source_char.related_video_links = ["https://test.com", "https://testing.com"]
        source_char.save()

        self.call_copy_site_command()

        target_char = Character.objects.get(site__slug=self.TARGET_SLUG)
        target_char_variant = CharacterVariant.objects.get(site__slug=self.TARGET_SLUG)

        assert target_char.title == source_char.title
        assert target_char.sort_order == source_char.sort_order
        assert target_char_variant.title == source_char_variant.title
        assert target_char_variant.base_character == target_char

        assert target_char.related_images.count() == 2
        assert target_char.related_videos.count() == 2
        assert target_char.related_audio.count() == 2

    def test_ignored_characters(self):
        source_ignored_char = IgnoredCharacterFactory(site=self.source_site)

        self.call_copy_site_command()

        target_ignored_char = IgnoredCharacter.objects.get(site__slug=self.TARGET_SLUG)

        assert target_ignored_char.title == source_ignored_char.title

    def test_alphabet(self):
        source_alphabet = AlphabetFactory(
            site=self.source_site, input_to_canonical_map="[{'in': '2', 'out': 'two'}]"
        )

        self.call_copy_site_command()

        target_alphabet = Alphabet.objects.get(site__slug=self.TARGET_SLUG)

        assert (
            target_alphabet.input_to_canonical_map
            == source_alphabet.input_to_canonical_map
        )

    def test_categories(self):
        # Removing default categories from source site
        Category.objects.filter(site=self.source_site).delete()

        # Adding new categories
        source_parent_category = ParentCategoryFactory(site=self.source_site)
        source_child_category_1 = ChildCategoryFactory(
            site=self.source_site, parent=source_parent_category
        )
        source_child_category_2 = ChildCategoryFactory(
            site=self.source_site, parent=source_parent_category
        )

        source_extra_category = ParentCategoryFactory(site=self.source_site)

        self.call_copy_site_command()

        assert Category.objects.filter(site__slug=self.TARGET_SLUG).count() == 4

        # parent category
        target_parent_category = Category.objects.filter(
            site__slug=self.TARGET_SLUG, children__isnull=False
        ).distinct()[0]
        assert target_parent_category.title == source_parent_category.title
        child_categories = target_parent_category.children.all()

        assert child_categories.count() == 2
        assert child_categories[0].title == source_child_category_1.title
        assert child_categories[1].title == source_child_category_2.title

        assert Category.objects.filter(
            site__slug=self.TARGET_SLUG, title=source_extra_category.title
        ).exists()

    def test_audio_and_speakers(self):
        source_speaker = PersonFactory(site=self.source_site)
        source_audio = AudioFactory(site=self.source_site)
        AudioSpeakerFactory(audio=source_audio, speaker=source_speaker)
        source_extra_person = PersonFactory(site=self.source_site)  # not a speaker

        self.call_copy_site_command()

        target_audio = Audio.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert target_audio.original != source_audio.original
        assert target_audio.title == source_audio.title

        target_speaker = target_audio.speakers.first()
        assert target_speaker.site.slug == self.TARGET_SLUG
        assert target_speaker.name == source_speaker.name

        assert Person.objects.filter(
            site__slug=self.TARGET_SLUG, name=source_extra_person.name
        ).exists()

    def test_images(self):
        source_image = ImageFactory(site=self.source_site)

        self.call_copy_site_command()

        target_image = Image.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert target_image.original != source_image.original
        assert target_image.title == source_image.title

        assert target_image.original.height == source_image.original.height
        assert target_image.original.width == source_image.original.width

        assert target_image.thumbnail is None
        assert target_image.small is None
        assert target_image.medium is None

    def test_videos(self):
        source_video = VideoFactory(site=self.source_site)

        self.call_copy_site_command()

        target_video = Video.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert target_video.original != source_video.original
        assert target_video.title == source_video.title

        assert target_video.original.height == source_video.original.height
        assert target_video.original.width == source_video.original.width

        assert target_video.thumbnail is None
        assert target_video.small is None
        assert target_video.medium is None

    def test_gallery(self):
        source_cover_img = ImageFactory(site=self.source_site)
        source_img_1 = ImageFactory(site=self.source_site)
        source_img_2 = ImageFactory(site=self.source_site)

        source_gallery = GalleryFactory(
            site=self.source_site, cover_image=source_cover_img
        )
        GalleryItemFactory.create(gallery=source_gallery, image=source_img_1)
        GalleryItemFactory.create(gallery=source_gallery, image=source_img_2)

        self.call_copy_site_command()

        target_gallery = Gallery.objects.filter(site__slug=self.TARGET_SLUG)[0]

        # Comparing titles and site for images as proxy
        # cover image
        assert target_gallery.cover_image.title == source_cover_img.title
        assert target_gallery.cover_image.site.slug == self.TARGET_SLUG

        target_gallery_item_1 = target_gallery.galleryitem_set.all().order_by(
            "ordering"
        )[0]
        target_gallery_item_2 = target_gallery.galleryitem_set.all().order_by(
            "ordering"
        )[1]

        assert target_gallery_item_1.image.title == source_img_1.title
        assert target_gallery_item_2.image.title == source_img_2.title

    def test_songs(self):
        source_img_1 = ImageFactory(site=self.source_site)
        source_img_2 = ImageFactory(site=self.source_site)
        source_video_1 = VideoFactory(site=self.source_site)
        source_video_2 = VideoFactory(site=self.source_site)
        source_audio_1 = AudioFactory(site=self.source_site)
        source_audio_2 = AudioFactory(site=self.source_site)

        source_song = SongFactory(site=self.source_site)
        source_lyric_1 = LyricsFactory(song=source_song)
        source_lyric_2 = LyricsFactory(song=source_song)

        source_song.related_images.set([source_img_1, source_img_2])
        source_song.related_videos.set([source_video_1, source_video_2])
        source_song.related_audio.set([source_audio_1, source_audio_2])
        source_song.related_video_links = ["https://test.com", "https://testing.com"]
        source_song.save()

        self.call_copy_site_command()

        target_song = Song.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert target_song.acknowledgements == source_song.acknowledgements
        assert target_song.notes == source_song.notes
        assert target_song.hide_overlay == source_song.hide_overlay
        assert target_song.exclude_from_games == source_song.exclude_from_games
        assert target_song.exclude_from_kids == source_song.exclude_from_kids
        assert target_song.visibility == source_song.visibility

        target_lyric_1 = target_song.lyrics.all()[0]
        target_lyric_2 = target_song.lyrics.all()[1]

        assert target_lyric_1.ordering == source_lyric_1.ordering
        assert target_lyric_2.ordering == source_lyric_2.ordering

        assert target_song.related_images.count() == 2
        assert target_song.related_videos.count() == 2
        assert target_song.related_audio.count() == 2
        assert target_song.related_video_links == source_song.related_video_links

    def test_stories(self):
        source_img_1 = ImageFactory(site=self.source_site)
        source_img_2 = ImageFactory(site=self.source_site)
        source_page_img_1 = ImageFactory(site=self.source_site)
        source_page_img_2 = ImageFactory(site=self.source_site)
        source_video_1 = VideoFactory(site=self.source_site)
        source_video_2 = VideoFactory(site=self.source_site)
        source_page_video_1 = VideoFactory(site=self.source_site)
        source_page_video_2 = VideoFactory(site=self.source_site)
        source_audio_1 = AudioFactory(site=self.source_site)
        source_audio_2 = AudioFactory(site=self.source_site)
        source_page_audio_1 = AudioFactory(site=self.source_site)
        source_page_audio_2 = AudioFactory(site=self.source_site)

        source_story = StoryFactory(site=self.source_site)
        source_story_page = StoryPageFactory(story=source_story)

        source_story.related_images.set([source_img_1, source_img_2])
        source_story.related_videos.set([source_video_1, source_video_2])
        source_story.related_audio.set([source_audio_1, source_audio_2])
        source_story.related_video_links = ["https://test.com", "https://testing.com"]
        source_story.save()

        source_story_page.related_images.set([source_page_img_1, source_page_img_2])
        source_story_page.related_videos.set([source_page_video_1, source_page_video_2])
        source_story_page.related_audio.set([source_page_audio_1, source_page_audio_2])
        source_story_page.save()

        self.call_copy_site_command()

        target_story = Story.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert target_story.acknowledgements == source_story.acknowledgements
        assert target_story.author == source_story.author
        assert target_story.notes == source_story.notes
        assert target_story.hide_overlay == source_story.hide_overlay
        assert target_story.exclude_from_games == source_story.exclude_from_games
        assert target_story.exclude_from_kids == source_story.exclude_from_kids
        assert target_story.visibility == source_story.visibility

        assert target_story.related_images.count() == 2
        assert target_story.related_videos.count() == 2
        assert target_story.related_audio.count() == 2
        assert target_story.related_video_links == source_story.related_video_links

        target_story_page = target_story.pages.all()[0]

        assert target_story_page.ordering == source_story_page.ordering
        assert target_story_page.notes == source_story_page.notes

        assert target_story_page.related_images.count() == 2
        assert target_story_page.related_videos.count() == 2
        assert target_story_page.related_audio.count() == 2

        target_story_page_img_1 = target_story_page.related_images.all().order_by(
            "created"
        )[0]
        target_story_page_img_2 = target_story_page.related_images.all().order_by(
            "created"
        )[1]
        target_story_page_video_1 = target_story_page.related_videos.all().order_by(
            "created"
        )[0]
        target_story_page_video_2 = target_story_page.related_videos.all().order_by(
            "created"
        )[1]
        target_story_page_audio_1 = target_story_page.related_audio.all().order_by(
            "created"
        )[0]
        target_story_page_audio_2 = target_story_page.related_audio.all().order_by(
            "created"
        )[1]

        assert target_story_page_img_1.title == source_page_img_1.title
        assert target_story_page_img_2.title == source_page_img_2.title
        assert target_story_page_video_1.title == source_page_video_1.title
        assert target_story_page_video_2.title == source_page_video_2.title
        assert target_story_page_audio_1.title == source_page_audio_1.title
        assert target_story_page_audio_2.title == source_page_audio_2.title

    def test_dictionary_entries(self):
        source_category_1 = ParentCategoryFactory(site=self.source_site)
        source_category_2 = ParentCategoryFactory(site=self.source_site)
        source_child_category = ChildCategoryFactory(
            site=self.source_site, parent=source_category_2
        )
        source_related_entry_1 = DictionaryEntryFactory(
            site=self.source_site, title="related entry 1"
        )
        source_related_entry_2 = DictionaryEntryFactory(
            site=self.source_site, title="related entry 2"
        )
        source_related_char_1 = CharacterFactory(site=self.source_site)
        source_related_char_2 = CharacterFactory(site=self.source_site)
        source_img_1 = ImageFactory(site=self.source_site)
        source_img_2 = ImageFactory(site=self.source_site)
        source_video_1 = VideoFactory(site=self.source_site)
        source_video_2 = VideoFactory(site=self.source_site)
        source_audio_1 = AudioFactory(site=self.source_site)
        source_audio_2 = AudioFactory(site=self.source_site)
        source_import_job = ImportJobFactory(site=self.source_site)

        source_entry = DictionaryEntryFactory(
            site=self.source_site,
            title="Primary entry",
            batch_id="validId",
            import_job=source_import_job,
        )

        source_entry.categories.set([source_category_1, source_child_category])
        source_entry.related_dictionary_entries.set(
            [source_related_entry_1, source_related_entry_2]
        )
        source_entry.related_characters.set(
            [source_related_char_1, source_related_char_2]
        )
        source_entry.related_images.set([source_img_1, source_img_2])
        source_entry.related_videos.set([source_video_1, source_video_2])
        source_entry.related_audio.set([source_audio_1, source_audio_2])
        source_entry.related_video_links = ["https://test.com", "https://testing.com"]
        source_entry.save()

        self.call_copy_site_command()

        target_entry = DictionaryEntry.objects.get(
            site__slug=self.TARGET_SLUG, title=source_entry.title
        )

        assert target_entry.type == source_entry.type
        assert target_entry.custom_order == source_entry.custom_order
        assert target_entry.exclude_from_wotd == source_entry.exclude_from_wotd
        assert target_entry.part_of_speech == source_entry.part_of_speech
        assert target_entry.split_chars_base == source_entry.split_chars_base
        assert target_entry.notes == source_entry.notes
        assert target_entry.acknowledgements == source_entry.acknowledgements
        assert target_entry.translations == source_entry.translations
        assert target_entry.alternate_spellings == source_entry.alternate_spellings
        assert target_entry.pronunciations == source_entry.pronunciations
        assert target_entry.batch_id == ""
        assert target_entry.import_job is None
        assert target_entry.exclude_from_games == source_entry.exclude_from_games
        assert target_entry.exclude_from_kids == source_entry.exclude_from_kids
        assert target_entry.visibility == source_entry.visibility

        target_categories = target_entry.categories.order_by("created").all()
        assert target_categories[0].title == source_category_1.title
        assert target_categories[0].site.slug == self.TARGET_SLUG
        assert target_categories[1].title == source_child_category.title
        assert target_categories[1].site.slug == self.TARGET_SLUG
        assert target_categories[1].parent.title == source_category_2.title

        target_related_entries = target_entry.related_dictionary_entries.order_by(
            "created"
        ).all()
        assert target_related_entries[0].title == source_related_entry_1.title
        assert target_related_entries[1].title == source_related_entry_2.title

        target_related_characters = target_entry.related_characters.order_by(
            "created"
        ).all()
        assert target_related_characters[0].title == source_related_char_1.title
        assert target_related_characters[1].title == source_related_char_2.title

        assert target_entry.related_images.count() == 2
        assert target_entry.related_videos.count() == 2
        assert target_entry.related_audio.count() == 2

    def test_immersion_labels(self):
        entry = DictionaryEntryFactory(site=self.source_site)
        source_imm_label = ImmersionLabelFactory(
            site=self.source_site, key="test key", dictionary_entry=entry
        )

        self.call_copy_site_command()

        target_imm_label = ImmersionLabel.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert target_imm_label.key == source_imm_label.key
        assert (
            target_imm_label.dictionary_entry.title
            == source_imm_label.dictionary_entry.title
        )

    def test_missing_audio_original(self, caplog):
        src_audio = AudioFactory(site=self.source_site)

        with patch("django.core.files.storage.Storage.open") as mock_open:
            mock_open.side_effect = FileNotFoundError
            self.call_copy_site_command()

        assert f"Couldn't copy audio file with id: {src_audio.id}" in caplog.text

    def test_missing_image_original(self, caplog):
        src_image = ImageFactory(site=self.source_site)

        with patch("django.core.files.storage.Storage.open") as mock_open:
            mock_open.side_effect = FileNotFoundError
            self.call_copy_site_command()

        assert f"Couldn't copy image file with id: {src_image.id}" in caplog.text

    def test_missing_video_original(self, caplog):
        src_video = VideoFactory(site=self.source_site)

        with patch("django.core.files.storage.Storage.open") as mock_open:
            mock_open.side_effect = FileNotFoundError
            self.call_copy_site_command()

        assert f"Couldn't copy video file with id: {src_video.id}" in caplog.text

    def test_gallery_associated_images_missing_original(self, caplog):
        src_image = ImageFactory(site=self.source_site)

        src_gallery = GalleryFactory(site=self.source_site, cover_image=src_image)
        GalleryItemFactory.create(gallery=src_gallery, image=src_image)

        with patch("django.core.files.storage.Storage.open") as mock_open:
            mock_open.side_effect = FileNotFoundError
            self.call_copy_site_command()

        assert (
            f"Missing gallery.cover.image in image map with id: {src_image.id}"
            in caplog.text
        )
        assert (
            f"Missing gallery_item.image in image map with id: {src_image.id}"
            in caplog.text
        )
