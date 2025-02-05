import logging
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.core.management.base import BaseCommand

from backend.models.category import Category
from backend.models.characters import (
    Alphabet,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from backend.models.dictionary import DictionaryEntry
from backend.models.files import File
from backend.models.galleries import Gallery, GalleryItem
from backend.models.immersion_labels import ImmersionLabel
from backend.models.media import Audio, Image, ImageFile, Person, Video, VideoFile
from backend.models.sites import Site, SiteFeature, SiteMenu
from backend.models.song import Song
from backend.models.story import Story


def get_object_or_raise_attribute_error(model, error, **filters):
    obj = model.objects.filter(**filters).first()
    if not obj:
        raise AttributeError(error)
    return obj


def verify_target_site_does_not_exist(target_slug, force_delete):
    if Site.objects.filter(slug=target_slug).exists():
        if force_delete:
            Site.objects.filter(slug=target_slug).delete()
        else:
            raise AttributeError(
                f"Site with slug {target_slug} already exists. Use --force-delete to override."
            )


def create_new_site(source_site, target_slug, user):
    new_site = Site(
        slug=target_slug,
        title=target_slug,
        language=source_site.language,
        visibility=source_site.visibility,
        is_hidden=source_site.is_hidden,
        created_by=user,
        last_modified_by=user,
        # contact_email_old
        # contact_emails
        # contact_users
        # homepage
        # logo
        # banner_image
        # banner_video
    )
    new_site.save()
    return new_site


def copy_related_objects(source_site, new_site):
    image_map = {}
    video_map = {}
    audio_map = {}
    category_map = {}
    character_map = {}
    dictionary_entry_map = {}

    site_features = SiteFeature.objects.filter(site=source_site)
    for site_feature in site_features:
        site_feature.id = uuid.uuid4()
        site_feature.site = new_site
        site_feature.save()

    site_menu_list = SiteMenu.objects.filter(site=source_site)
    for site_menu in site_menu_list:
        site_menu.id = uuid.uuid4()
        site_menu.site = new_site
        site_menu.save()

    characters = Character.objects.filter(site=source_site)
    for character in characters:
        variants = CharacterVariant.objects.filter(base_character=character)

        old_char_id = character.id
        new_char_id = uuid.uuid4()
        character_map[old_char_id] = new_char_id

        character.id = new_char_id
        character.site = new_site
        character.save()

        # Variants
        for variant in variants:
            variant.id = uuid.uuid4()
            variant.site = new_site
            variant.base_character = character
            variant.save()

    ignored_characters = IgnoredCharacter.objects.filter(site=source_site)
    for ignored_character in ignored_characters:
        ignored_character.id = uuid.uuid4()
        ignored_character.site = new_site
        ignored_character.save()

    alphabets = Alphabet.objects.filter(site=source_site)
    for alphabet in alphabets:
        alphabet.id = uuid.uuid4()
        alphabet.site = new_site
        alphabet.save()

    # Removing auto-generated categories
    Category.objects.filter(site=new_site).delete()
    # Copy over all the parent categories
    categories = Category.objects.filter(
        site=source_site, children__isnull=False
    ).distinct()
    for category in categories:
        child_categories = category.children.all()
        for child_category in child_categories:
            old_category_id = child_category.id
            new_category_id = uuid.uuid4()
            category_map[old_category_id] = new_category_id

            child_category.id = new_category_id
            child_category.site = new_site
            child_category.save()

        old_category_id = category.id
        new_category_id = uuid.uuid4()
        category_map[old_category_id] = new_category_id

        category.id = new_category_id
        category.site = new_site
        category.save()

        for child_category in child_categories:
            child_category.parent = category
            child_category.save()

    # Updated category list, copying over rest of categories
    new_site_categories = Category.objects.filter(site=new_site).values_list(
        "title", flat=True
    )
    categories = (
        Category.objects.filter(site=source_site)
        .exclude(title__in=new_site_categories)
        .distinct()
    )
    for category in categories:
        old_category_id = category.id
        new_category_id = uuid.uuid4()
        category_map[old_category_id] = new_category_id

        category.id = new_category_id
        category.site = new_site
        category.save()

    audio_files = Audio.objects.filter(site=source_site)
    for audio_file in audio_files:
        # Content
        new_file = File(
            content=UploadedFile(audio_file.original.content.file),
            site=new_site,
        )
        new_file.save()
        audio_file.original = new_file

        # Speakers
        current_speakers = audio_file.speakers.all()
        new_speakers = []
        for person in current_speakers:
            person.id = uuid.uuid4()
            person.site = new_site
            person.save()
            new_speakers.append(person)

        audio_file.site = new_site

        old_audio_id = audio_file.id
        new_audio_id = uuid.uuid4()
        audio_map[old_audio_id] = new_audio_id

        audio_file.id = new_audio_id
        # To circumvent checks added to media models to prevent modification of original file
        audio_file._state.adding = True
        audio_file.save()

        audio_file.speakers.set(new_speakers)

    # Copy over rest of the people who are not attached as speakers to any audio
    person_list = Person.objects.filter(site=source_site, audio_set__isnull=True)
    for person in person_list:
        person.id = uuid.uuid4()
        person.site = new_site
        person.save()

    image_files = Image.objects.filter(site=source_site)
    for image_file in image_files:
        # Content
        new_file = ImageFile(
            content=UploadedFile(image_file.original.content.file),
            site=new_site,
        )
        new_file.save()
        image_file.original = new_file

        image_file.thumbnail = None
        image_file.small = None
        image_file.medium = None
        image_file.site = new_site

        old_img_id = image_file.id
        new_img_id = uuid.uuid4()
        image_map[old_img_id] = new_img_id

        image_file.id = new_img_id
        image_file._state.adding = True
        image_file.save()

    video_files = Video.objects.filter(site=source_site)
    for video_file in video_files:
        # Content
        new_file = VideoFile(
            content=UploadedFile(video_file.original.content.file),
            site=new_site,
        )
        new_file.save()
        video_file.original = new_file

        video_file.thumbnail = None
        video_file.small = None
        video_file.medium = None
        video_file.site = new_site

        old_video_id = video_file.id
        new_video_id = uuid.uuid4()
        video_map[old_video_id] = new_video_id

        video_file.id = new_video_id
        video_file._state.adding = True
        video_file.save()

    galleries = Gallery.objects.filter(site=source_site)
    for gallery in galleries:
        gallery_items = list(gallery.galleryitem_set.all())

        gallery.site = new_site

        new_cover_img_id = image_map[gallery.cover_image.id]
        gallery.cover_image = Image.objects.get(id=new_cover_img_id)

        gallery.id = uuid.uuid4()
        gallery.save()

        updated_gallery_items = []
        for gallery_item in gallery_items:
            new_gallery_item = GalleryItem(
                gallery=gallery,
                image=Image.objects.get(id=image_map[gallery_item.image.id]),
                ordering=gallery_item.ordering,
            )
            new_gallery_item.save()
            updated_gallery_items.append(new_gallery_item)

        gallery.galleryitem_set.set(updated_gallery_items)
        gallery.save()

    songs = Song.objects.filter(site=source_site)
    for song in songs:
        old_lyrics = list(song.lyrics.all())
        old_images = list(song.related_images.all())
        old_videos = list(song.related_videos.all())
        old_audio = list(song.related_audio.all())

        song.id = uuid.uuid4()
        song.site = new_site
        song.save()

        for lyric in old_lyrics:
            lyric.id = uuid.uuid4()
            lyric.song = song
            lyric.save()

        # related media
        new_images = []
        for image in old_images:
            new_images.append(image_map[image.id])

        new_videos = []
        for video in old_videos:
            new_videos.append(video_map[video.id])

        new_audio = []
        for audio in old_audio:
            new_audio.append(audio_map[audio.id])

        song.related_images.set(new_images)
        song.related_videos.set(new_videos)
        song.related_audio.set(new_audio)
        song.save()

    stories = Story.objects.filter(site=source_site)
    for story in stories:
        old_pages = list(story.pages.all())
        old_images = list(story.related_images.all())
        old_videos = list(story.related_videos.all())
        old_audio = list(story.related_audio.all())

        story.id = uuid.uuid4()
        story.site = new_site
        story.save()

        # Related media on story
        new_images = []
        for image in old_images:
            new_images.append(image_map[image.id])

        new_videos = []
        for video in old_videos:
            new_videos.append(video_map[video.id])

        new_audio = []
        for audio in old_audio:
            new_audio.append(audio_map[audio.id])

        story.related_images.set(new_images)
        story.related_videos.set(new_videos)
        story.related_audio.set(new_audio)
        story.save()

        for page in old_pages:
            old_images = list(page.related_images.all())
            old_videos = list(page.related_videos.all())
            old_audio = list(page.related_audio.all())
            page.id = uuid.uuid4()
            page.story = story
            page.save()

            # Related media on story page
            new_images = []
            for image in old_images:
                new_images.append(image_map[image.id])

            new_videos = []
            for video in old_videos:
                new_videos.append(video_map[video.id])

            new_audio = []
            for audio in old_audio:
                new_audio.append(audio_map[audio.id])

            page.related_images.set(new_images)
            page.related_videos.set(new_videos)
            page.related_audio.set(new_audio)
            page.save()

    # Copying over dictionary entries which don't have related_entries
    dictionary_entries = DictionaryEntry.objects.filter(
        site=source_site, related_dictionary_entries__isnull=True
    ).distinct()
    for entry in dictionary_entries:
        old_categories = list(entry.categories.all())
        old_related_characters = list(entry.related_characters.all())
        old_images = list(entry.related_images.all())
        old_videos = list(entry.related_videos.all())
        old_audio = list(entry.related_audio.all())

        old_entry_id = entry.id
        new_entry_id = uuid.uuid4()
        dictionary_entry_map[old_entry_id] = new_entry_id

        entry.id = new_entry_id
        entry.site = new_site
        entry.batch_id = ""
        entry.import_job = None
        entry.save()

        new_categories = []
        for category in old_categories:
            new_categories.append(Category.objects.get(id=category_map[category.id]))
        entry.categories.set(new_categories)

        new_related_characters = []
        for char in old_related_characters:
            new_related_characters.append(
                Character.objects.get(id=character_map[char.id])
            )
        entry.related_characters.set(new_related_characters)

        new_images = []
        for image in old_images:
            new_images.append(image_map[image.id])

        new_videos = []
        for video in old_videos:
            new_videos.append(video_map[video.id])

        new_audio = []
        for audio in old_audio:
            new_audio.append(audio_map[audio.id])

        entry.related_images.set(new_images)
        entry.related_videos.set(new_videos)
        entry.related_audio.set(new_audio)
        entry.save()

    dictionary_entries = DictionaryEntry.objects.filter(
        site=source_site, related_dictionary_entries__isnull=False
    ).distinct()
    for entry in dictionary_entries:
        old_categories = list(entry.categories.all())
        old_related_entries = list(entry.related_dictionary_entries.all())
        old_related_characters = list(entry.related_characters.all())
        old_images = list(entry.related_images.all())
        old_videos = list(entry.related_videos.all())
        old_audio = list(entry.related_audio.all())

        old_entry_id = entry.id
        new_entry_id = uuid.uuid4()
        dictionary_entry_map[old_entry_id] = new_entry_id

        entry.id = new_entry_id
        entry.site = new_site
        entry.batch_id = ""
        entry.import_job = None
        entry.save()

        new_categories = []
        for category in old_categories:
            new_categories.append(Category.objects.get(id=category_map[category.id]))
        entry.categories.set(new_categories)

        new_related_entries = []
        for related_entry in old_related_entries:
            new_related_entries.append(
                DictionaryEntry.objects.get(id=dictionary_entry_map[related_entry.id])
            )
        entry.related_dictionary_entries.set(new_related_entries)

        new_related_characters = []
        for char in old_related_characters:
            new_related_characters.append(
                Character.objects.get(id=character_map[char.id])
            )
        entry.related_characters.set(new_related_characters)

        new_images = []
        for image in old_images:
            new_images.append(image_map[image.id])

        new_videos = []
        for video in old_videos:
            new_videos.append(video_map[video.id])

        new_audio = []
        for audio in old_audio:
            new_audio.append(audio_map[audio.id])

        entry.related_images.set(new_images)
        entry.related_videos.set(new_videos)
        entry.related_audio.set(new_audio)
        entry.save()

    # Maybe try to sort these in a way so that all entries which don't have a related entry are copied
    # over first so then we don't have to run 2 loops
    # verify if we want to clear out batch_id and import_job field

    imm_labels = ImmersionLabel.objects.filter(site=source_site)
    for imm_label in imm_labels:
        imm_label.id = uuid.uuid4()
        imm_label.site = new_site

        curr_dictionary_entry = imm_label.dictionary_entry
        new_dictionary_entry = DictionaryEntry.objects.get(
            id=dictionary_entry_map[curr_dictionary_entry.id]
        )
        imm_label.dictionary_entry = new_dictionary_entry

        imm_label.save()

    # List of stuff to be generated and/or copied over.
    """
        Required
        - Widget, WidgetSettings, SiteWidgetList, SiteWidgetListOrder
        - SitePage
    """


class Command(BaseCommand):
    help = "Copy a Site and all its contents from a source slug to a target slug."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            dest="source_slug",
            help="Site slug of the site to copy from.",
            required=True,
        )
        parser.add_argument(
            "--target",
            dest="target_slug",
            help="Site slug of the site to copy to.",
            required=True,
        )
        parser.add_argument(
            "--email",
            dest="email",
            help="User to be used for created and modified fields.",
            required=True,
        )
        parser.add_argument(
            "--force-delete",
            dest="force_delete",
            help="Delete target site if exists.",
            action="store_true",
        )
        # parser.add_argument(
        #     "--title",
        #     dest="title",
        #     help="Title of the newly created site.",
        #     required=True,
        # )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)

        source_slug = options["source_slug"]
        target_slug = options["target_slug"]
        user_email = options["email"]
        force_delete = options["force_delete"]

        logger.info("Verifying requirements.")

        source_site = get_object_or_raise_attribute_error(
            Site, slug=source_slug, error="Provided source site does not exist."
        )
        user = get_object_or_raise_attribute_error(
            get_user_model(),
            email=user_email,
            error="No user found with the provided email.",
        )
        verify_target_site_does_not_exist(target_slug, force_delete)

        logger.info(
            f"Creating new site: {target_slug} and copying content from {source_slug}."
        )

        new_site = create_new_site(source_site, target_slug, user)

        copy_related_objects(source_site, new_site)
        logger.info("Site copy completed successfully.")

        # Memberships ?
        # JoinRequest & JoinRequestReason ?

        # to keep track of copied over media

        # Index the site and all the copied over stuff
