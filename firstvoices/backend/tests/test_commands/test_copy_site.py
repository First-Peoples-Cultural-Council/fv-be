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
from backend.models.galleries import Gallery
from backend.models.media import Audio, Image, Person, Video
from backend.models.sites import Site, SiteFeature, SiteMenu
from backend.models.song import Song
from backend.models.story import Story
from backend.tests.factories import (
    AlphabetFactory,
    AudioFactory,
    AudioSpeakerFactory,
    CharacterFactory,
    CharacterVariantFactory,
    ChildCategoryFactory,
    GalleryFactory,
    GalleryItemFactory,
    IgnoredCharacterFactory,
    ImageFactory,
    LyricsFactory,
    ParentCategoryFactory,
    PersonFactory,
    SiteFactory,
    SiteFeatureFactory,
    SiteMenuFactory,
    SongFactory,
    StoryFactory,
    StoryPageFactory,
    VideoFactory,
    get_app_admin,
)


@pytest.mark.django_db
class TestCopySite:
    SOURCE_SLUG = "old"
    TARGET_SLUG = "new"

    def setup_method(self):
        self.old_site = SiteFactory.create(slug=self.SOURCE_SLUG, title="old")
        self.user = get_app_admin(AppRole.SUPERADMIN)

    def call_default_command(self):
        # helper function
        call_command(
            "copy_site",
            source_slug=self.SOURCE_SLUG,
            target_slug=self.TARGET_SLUG,
            email=self.user.email,
        )

    def test_source_site_exists(self):
        with pytest.raises(AttributeError) as e:
            call_command(
                "copy_site",
                source_slug="does_not_exist",
                target_slug=self.TARGET_SLUG,
                email=self.user.email,
            )
        assert str(e.value) == "Provided source site does not exist."

    def test_target_site_does_not_exist(self):
        SiteFactory.create(slug=self.TARGET_SLUG)
        with pytest.raises(AttributeError) as e:
            self.call_default_command()
        assert (
            str(e.value)
            == f"Site with slug {self.TARGET_SLUG} already exists. Use --force-delete to override."
        )

    def test_target_user_does_not_exist(self):
        with pytest.raises(AttributeError) as e:
            call_command(
                "copy_site",
                source_slug=self.SOURCE_SLUG,
                target_slug=self.TARGET_SLUG,
                email="notareal@email.com",
            )
        assert str(e.value) == "No user found with the provided email."

    def test_new_site_attributes(self):
        self.call_default_command()

        old_site = Site.objects.get(slug=self.SOURCE_SLUG)
        new_site = Site.objects.get(slug=self.TARGET_SLUG)

        assert new_site.title == self.TARGET_SLUG
        assert new_site.language == old_site.language
        assert new_site.visibility == old_site.visibility
        assert new_site.is_hidden == old_site.is_hidden

        assert new_site.created_by.email == self.user.email
        assert new_site.last_modified_by.email == self.user.email

    def test_site_features(self):
        sf_1 = SiteFeatureFactory.create(
            site=self.old_site, key="first_feature", is_enabled=True
        )
        sf_2 = SiteFeatureFactory.create(
            site=self.old_site, key="second_feature", is_enabled=False
        )

        self.call_default_command()

        sf_1_new = SiteFeature.objects.get(
            site__slug=self.TARGET_SLUG, key="first_feature"
        )
        sf_2_new = SiteFeature.objects.get(
            site__slug=self.TARGET_SLUG, key="second_feature"
        )

        assert sf_1_new.is_enabled == sf_1.is_enabled
        assert sf_2_new.is_enabled == sf_2.is_enabled

    def test_site_menu(self):
        old_site_menu = SiteMenuFactory.create(site=self.old_site)

        self.call_default_command()

        new_site_menu = SiteMenu.objects.get(site__slug=self.TARGET_SLUG)

        assert new_site_menu.json == old_site_menu.json

    def test_characters_and_variants(self):
        old_char = CharacterFactory(site=self.old_site)
        old_char_variant = CharacterVariantFactory(
            site=self.old_site, base_character=old_char
        )

        self.call_default_command()

        new_char = Character.objects.get(site__slug=self.TARGET_SLUG)
        new_char_variant = CharacterVariant.objects.get(site__slug=self.TARGET_SLUG)

        assert new_char.title == old_char.title
        assert new_char.sort_order == old_char.sort_order
        assert new_char_variant.title == old_char_variant.title
        assert new_char_variant.base_character == new_char

    def test_ignored_characters(self):
        old_char = IgnoredCharacterFactory(site=self.old_site)

        self.call_default_command()

        new_char = IgnoredCharacter.objects.get(site__slug=self.TARGET_SLUG)

        assert new_char.title == old_char.title

    def test_alphabet(self):
        old_alphabet = AlphabetFactory(
            site=self.old_site, input_to_canonical_map="[{'in': '2', 'out': 'two'}]"
        )

        self.call_default_command()

        new_alphabet = Alphabet.objects.get(site__slug=self.TARGET_SLUG)

        assert (
            new_alphabet.input_to_canonical_map == old_alphabet.input_to_canonical_map
        )

    def test_category(self):
        # Removing default categories from old site
        Category.objects.filter(site=self.old_site).delete()

        # Adding new categories
        old_parent_category = ParentCategoryFactory(site=self.old_site)
        old_child_category_1 = ChildCategoryFactory(
            site=self.old_site, parent=old_parent_category
        )
        old_child_category_2 = ChildCategoryFactory(
            site=self.old_site, parent=old_parent_category
        )

        old_extra_category = ParentCategoryFactory(site=self.old_site)

        self.call_default_command()

        assert Category.objects.filter(site__slug=self.TARGET_SLUG).count() == 4

        # parent category
        new_parent_category = Category.objects.filter(
            site__slug=self.TARGET_SLUG, children__isnull=False
        ).distinct()[0]
        assert new_parent_category.title == old_parent_category.title
        child_categories = new_parent_category.children.all()

        assert child_categories.count() == 2
        assert child_categories[0].title == old_child_category_1.title
        assert child_categories[1].title == old_child_category_2.title

        assert Category.objects.filter(
            site__slug=self.TARGET_SLUG, title=old_extra_category.title
        ).exists()

    def test_audio_and_speakers(self):
        old_speaker = PersonFactory(site=self.old_site)
        old_audio = AudioFactory(site=self.old_site)
        AudioSpeakerFactory(audio=old_audio, speaker=old_speaker)
        old_extra = PersonFactory(site=self.old_site)  # not a speaker

        self.call_default_command()

        new_audio = Audio.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert new_audio.original != old_audio.original
        assert new_audio.title == old_audio.title

        new_speaker = new_audio.speakers.first()
        assert new_speaker.site.slug == self.TARGET_SLUG
        assert new_speaker.name == old_speaker.name

        assert Person.objects.filter(
            site__slug=self.TARGET_SLUG, name=old_extra.name
        ).exists()

    def test_images(self):
        old_image = ImageFactory(site=self.old_site)

        self.call_default_command()

        new_image = Image.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert new_image.original != old_image.original
        assert new_image.title == old_image.title

        assert new_image.original.height == old_image.original.height
        assert new_image.original.width == old_image.original.width

        assert new_image.thumbnail is None
        assert new_image.small is None
        assert new_image.medium is None

    def test_videos(self):
        old_video = VideoFactory(site=self.old_site)

        self.call_default_command()

        new_video = Video.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert new_video.original != old_video.original
        assert new_video.title == old_video.title

        assert new_video.original.height == old_video.original.height
        assert new_video.original.width == old_video.original.width

        assert old_video.thumbnail is None
        assert old_video.small is None
        assert old_video.medium is None

    def test_gallery(self):
        cover_img = ImageFactory(site=self.old_site)
        img_1 = ImageFactory(site=self.old_site)
        img_2 = ImageFactory(site=self.old_site)

        old_gallery = GalleryFactory(site=self.old_site, cover_image=cover_img)
        GalleryItemFactory.create(gallery=old_gallery, image=img_1)
        GalleryItemFactory.create(gallery=old_gallery, image=img_2)

        self.call_default_command()

        new_gallery = Gallery.objects.filter(site__slug=self.TARGET_SLUG)[0]

        # Comparing titles and site for images as proxy
        # cover image
        assert new_gallery.cover_image.title == cover_img.title
        assert new_gallery.cover_image.site.slug == self.TARGET_SLUG

        gallery_item_1 = new_gallery.galleryitem_set.all().order_by("ordering")[0]
        gallery_item_2 = new_gallery.galleryitem_set.all().order_by("ordering")[1]

        assert gallery_item_1.image.title == img_1.title
        assert gallery_item_2.image.title == img_2.title

    def test_song(self):
        img_1 = ImageFactory(site=self.old_site)
        img_2 = ImageFactory(site=self.old_site)
        video_1 = VideoFactory(site=self.old_site)
        video_2 = VideoFactory(site=self.old_site)
        audio_1 = AudioFactory(site=self.old_site)
        audio_2 = AudioFactory(site=self.old_site)

        old_song = SongFactory(site=self.old_site)
        old_lyric_1 = LyricsFactory(song=old_song)
        old_lyric_2 = LyricsFactory(song=old_song)

        old_song.related_images.add(img_1)
        old_song.related_images.add(img_2)
        old_song.related_videos.add(video_1)
        old_song.related_videos.add(video_2)
        old_song.related_audio.add(audio_1)
        old_song.related_audio.add(audio_2)
        old_song.related_video_links = ["https://test.com", "https://testing.com"]
        old_song.save()

        self.call_default_command()

        new_song = Song.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert new_song.acknowledgements == old_song.acknowledgements
        assert new_song.notes == old_song.notes
        assert new_song.hide_overlay == old_song.hide_overlay

        new_lyric_1 = new_song.lyrics.all()[0]
        new_lyric_2 = new_song.lyrics.all()[1]

        assert new_lyric_1.ordering == old_lyric_1.ordering
        assert new_lyric_2.ordering == old_lyric_2.ordering

        assert new_song.related_images.all().count() == 2
        assert new_song.related_videos.all().count() == 2
        assert new_song.related_audio.all().count() == 2
        assert new_song.related_video_links == old_song.related_video_links

    def test_story(self):
        img_1 = ImageFactory(site=self.old_site)
        img_2 = ImageFactory(site=self.old_site)
        page_img_1 = ImageFactory(site=self.old_site)
        page_img_2 = ImageFactory(site=self.old_site)
        video_1 = VideoFactory(site=self.old_site)
        video_2 = VideoFactory(site=self.old_site)
        page_video_1 = VideoFactory(site=self.old_site)
        page_video_2 = VideoFactory(site=self.old_site)
        audio_1 = AudioFactory(site=self.old_site)
        audio_2 = AudioFactory(site=self.old_site)
        page_audio_1 = AudioFactory(site=self.old_site)
        page_audio_2 = AudioFactory(site=self.old_site)

        old_story = StoryFactory(site=self.old_site)
        old_page = StoryPageFactory(story=old_story)

        old_story.related_images.add(img_1)
        old_story.related_images.add(img_2)
        old_story.related_videos.add(video_1)
        old_story.related_videos.add(video_2)
        old_story.related_audio.add(audio_1)
        old_story.related_audio.add(audio_2)
        old_story.related_video_links = ["https://test.com", "https://testing.com"]
        old_story.save()

        old_page.related_images.add(page_img_1)
        old_page.related_images.add(page_img_2)
        old_page.related_videos.add(page_video_1)
        old_page.related_videos.add(page_video_2)
        old_page.related_audio.add(page_audio_1)
        old_page.related_audio.add(page_audio_2)
        old_page.save()

        self.call_default_command()

        new_story = Story.objects.filter(site__slug=self.TARGET_SLUG)[0]

        assert new_story.acknowledgements == old_story.acknowledgements
        assert new_story.author == old_story.author
        assert new_story.notes == old_story.notes
        assert new_story.hide_overlay == old_story.hide_overlay

        assert new_story.related_images.all().count() == 2
        assert new_story.related_videos.all().count() == 2
        assert new_story.related_audio.all().count() == 2
        assert new_story.related_video_links == old_story.related_video_links

        new_page = new_story.pages.all()[0]

        assert new_page.ordering == old_page.ordering
        assert new_page.notes == old_page.notes

        assert new_page.related_images.all().count() == 2
        assert new_page.related_videos.all().count() == 2
        assert new_page.related_audio.all().count() == 2

        new_page_img_1 = new_page.related_images.all().order_by("created")[0]
        new_page_img_2 = new_page.related_images.all().order_by("created")[1]
        new_page_video_1 = new_page.related_videos.all().order_by("created")[0]
        new_page_video_2 = new_page.related_videos.all().order_by("created")[1]
        new_page_audio_1 = new_page.related_audio.all().order_by("created")[0]
        new_page_audio_2 = new_page.related_audio.all().order_by("created")[1]

        assert new_page_img_1.title == page_img_1.title
        assert new_page_img_2.title == page_img_2.title
        assert new_page_video_1.title == page_video_1.title
        assert new_page_video_2.title == page_video_2.title
        assert new_page_audio_1.title == page_audio_1.title
        assert new_page_audio_2.title == page_audio_2.title
