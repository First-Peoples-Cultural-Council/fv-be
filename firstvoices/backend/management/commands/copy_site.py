import logging
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.core.management.base import BaseCommand
from django.db.models import Count

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
from backend.models.sites import Site, SiteFeature
from backend.models.song import Song
from backend.models.story import Story


def get_valid_object(model, error, **filters):
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


def create_new_site(source_site, target_site_slug, user):
    new_site = Site(
        slug=target_site_slug,
        title=target_site_slug,
        language=source_site.language,
        visibility=source_site.visibility,
        is_hidden=source_site.is_hidden,
        created_by=user,
        last_modified_by=user,
    )

    new_site.contact_users.clear()
    new_site.save()
    return new_site


def copy_site_features(source_site, target_site):
    site_features = list(SiteFeature.objects.filter(site=source_site))
    for site_feature in site_features:
        site_feature.id = uuid.uuid4()
        site_feature.site = target_site
        site_feature.save()


def copy_all_characters_and_return_map(
    source_site, target_site, audio_map, image_map, video_map
):
    character_map = {}
    characters = list(Character.objects.filter(site=source_site))

    for character in characters:
        source_media = {
            "audio": list(character.related_audio.all().values_list("id", flat=True)),
            "images": list(character.related_images.all().values_list("id", flat=True)),
            "videos": list(character.related_videos.all().values_list("id", flat=True)),
        }

        source_char_id = character.id
        target_char_id = uuid.uuid4()
        character_map[source_char_id] = target_char_id

        character.id = target_char_id
        character.site = target_site
        character.save()

        copy_related_media(character, source_media, audio_map, image_map, video_map)
        character.save()

    variants = list(CharacterVariant.objects.filter(site=source_site))
    for variant in variants:
        source_base_character = variant.base_character

        variant.id = uuid.uuid4()
        variant.site = target_site
        variant.base_character_id = character_map[source_base_character.id]
        variant.save()

    ignored_characters = list(IgnoredCharacter.objects.filter(site=source_site))
    for ignored_character in ignored_characters:
        ignored_character.id = uuid.uuid4()
        ignored_character.site = target_site
        ignored_character.save()

    return character_map


def copy_alphabet(source_site, target_site):
    alphabets = list(Alphabet.objects.filter(site=source_site))
    for alphabet in alphabets:
        alphabet.id = uuid.uuid4()
        alphabet.site = target_site
        alphabet.save()


def copy_categories_and_return_map(source_site, target_site, user):
    category_map = {}

    # Removing auto-generated categories
    Category.objects.filter(site=target_site).delete()
    # Copy over all the parent categories
    categories = list(
        Category.objects.filter(site=source_site, children__isnull=False).distinct()
    )
    for category in categories:
        child_categories = list(category.children.all())
        for child_category in child_categories:
            source_category_id = child_category.id
            target_category_id = uuid.uuid4()
            category_map[source_category_id] = target_category_id

            child_category.id = target_category_id
            child_category.site = target_site
            child_category.created_by = user
            child_category.last_modified_by = user
            child_category.save()

        source_category_id = category.id
        target_category_id = uuid.uuid4()
        category_map[source_category_id] = target_category_id

        category.id = target_category_id
        category.site = target_site
        category.created_by = user
        category.last_modified_by = user
        category.save()

        for child_category in child_categories:
            child_category.parent = category
            child_category.created_by = user
            child_category.last_modified_by = user
            child_category.save()

    # Updated category list, copying over rest of categories
    target_site_copied_over_categories = list(
        Category.objects.filter(site=target_site).values_list("title", flat=True)
    )
    categories = list(
        Category.objects.filter(site=source_site)
        .exclude(title__in=target_site_copied_over_categories)
        .distinct()
    )
    for category in categories:
        source_category_id = category.id
        target_category_id = uuid.uuid4()
        category_map[source_category_id] = target_category_id

        category.id = target_category_id
        category.site = target_site
        category.created_by = user
        category.last_modified_by = user
        category.save()

    return category_map


def copy_audio_and_speakers_and_return_map(source_site, target_site, logger):
    audio_map = {}

    audio_files = list(Audio.objects.filter(site=source_site))
    for audio_file in audio_files:
        try:
            target_file = File(
                content=UploadedFile(audio_file.original.content.file),
                site=target_site,
            )
            target_file.save()
            audio_file.original = target_file

            # Speakers
            current_speakers = list(audio_file.speakers.all())
            updated_speakers = []
            for person in current_speakers:
                person.id = uuid.uuid4()
                person.site = target_site
                person.save()
                updated_speakers.append(person)

            audio_file.site = target_site

            source_audio_id = audio_file.id
            target_audio_id = uuid.uuid4()
            audio_map[source_audio_id] = target_audio_id

            audio_file.id = target_audio_id
            # To circumvent checks added to media models to prevent modification of original file
            audio_file._state.adding = True
            audio_file.save()

            audio_file.speakers.set(updated_speakers)
        except Exception as e:
            logger.warning(f"Couldn't copy audio file with id: {audio_file.id}", e)

    # Copy over rest of the people who are not attached as speakers to any audio
    person_list = list(Person.objects.filter(site=source_site, audio_set__isnull=True))
    for person in person_list:
        person.id = uuid.uuid4()
        person.site = target_site
        person.save()

    return audio_map


def copy_images_and_return_map(source_site, target_site, logger):
    image_map = {}

    image_files = list(Image.objects.filter(site=source_site))
    for image_file in image_files:
        try:
            # Content
            target_file = ImageFile(
                content=UploadedFile(image_file.original.content.file),
                site=target_site,
            )
            target_file.save()
            image_file.original = target_file

            image_file.thumbnail = None
            image_file.small = None
            image_file.medium = None
            image_file.site = target_site

            source_img_id = image_file.id
            target_img_id = uuid.uuid4()
            image_map[source_img_id] = target_img_id

            image_file.id = target_img_id
            image_file._state.adding = True
            image_file.save()
        except Exception as e:
            logger.warning(f"Couldn't copy image file with id: {image_file.id}", e)

    return image_map


def copy_videos_and_return_map(source_site, target_site, logger):
    video_map = {}

    video_files = list(Video.objects.filter(site=source_site))
    for video_file in video_files:
        try:
            # Content
            target_file = VideoFile(
                content=UploadedFile(video_file.original.content.file),
                site=target_site,
            )
            target_file.save()
            video_file.original = target_file

            video_file.thumbnail = None
            video_file.small = None
            video_file.medium = None
            video_file.site = target_site

            source_video_id = video_file.id
            target_video_id = uuid.uuid4()
            video_map[source_video_id] = target_video_id

            video_file.id = target_video_id
            video_file._state.adding = True
            video_file.save()
        except Exception as e:
            logger.warning(f"Couldn't copy video file with id: {video_file.id}", e)

    return video_map


def copy_galleries(source_site, target_site, image_map, logger):
    galleries = list(Gallery.objects.filter(site=source_site))
    for gallery in galleries:
        gallery_items = list(gallery.galleryitem_set.all())

        gallery.site = target_site
        if gallery.cover_image.id not in image_map:
            logger.warning(
                f"Missing gallery.cover.image in image map with id: {gallery.cover_image.id}"
            )
        gallery.cover_image_id = image_map[gallery.cover_image.id]

        gallery.id = uuid.uuid4()
        gallery.save()

        updated_gallery_items = []
        for gallery_item in gallery_items:
            if gallery_item.image.id not in image_map:
                logger.warning(
                    f"Missing gallery_item.image in image map with id: {gallery_item.image.id}"
                )
                continue

            new_gallery_item = GalleryItem(
                gallery=gallery,
                image_id=image_map[gallery_item.image.id],
                ordering=gallery_item.ordering,
            )
            new_gallery_item.save()
            updated_gallery_items.append(new_gallery_item)

        gallery.galleryitem_set.set(updated_gallery_items)
        gallery.save()


def copy_related_media(instance, source_media, audio_map, image_map, video_map):
    # If the media is missing the original, that media file is not copied, and thus
    # also not added to the m2m for an instance
    target_images = [
        image_map[image_id]
        for image_id in source_media["images"]
        if image_id in image_map
    ]
    target_videos = [
        video_map[video_id]
        for video_id in source_media["videos"]
        if video_id in video_map
    ]
    target_audio = [
        audio_map[audio_id]
        for audio_id in source_media["audio"]
        if audio_id in audio_map
    ]

    if target_images:
        instance.related_images.set(target_images)
    if target_videos:
        instance.related_videos.set(target_videos)
    if target_audio:
        instance.related_audio.set(target_audio)
    instance.save()


def copy_songs(source_site, target_site, audio_map, image_map, video_map):
    songs = list(Song.objects.filter(site=source_site))
    for song in songs:
        source_lyrics = list(song.lyrics.all())
        source_media = {
            "audio": list(song.related_audio.all().values_list("id", flat=True)),
            "images": list(song.related_images.all().values_list("id", flat=True)),
            "videos": list(song.related_videos.all().values_list("id", flat=True)),
        }

        song.id = uuid.uuid4()
        song.site = target_site
        song.save()

        for lyric in source_lyrics:
            lyric.id = uuid.uuid4()
            lyric.song = song
            lyric.save()

        copy_related_media(song, source_media, audio_map, image_map, video_map)
        song.save()


def copy_stories(source_site, target_site, audio_map, image_map, video_map):
    stories = list(Story.objects.filter(site=source_site))
    for story in stories:
        source_pages = list(story.pages.all())
        source_media = {
            "audio": list(story.related_audio.all().values_list("id", flat=True)),
            "images": list(story.related_images.all().values_list("id", flat=True)),
            "videos": list(story.related_videos.all().values_list("id", flat=True)),
        }

        story.id = uuid.uuid4()
        story.site = target_site
        story.save()

        copy_related_media(story, source_media, audio_map, image_map, video_map)
        story.save()

        for page in source_pages:
            source_media = {
                "audio": list(page.related_audio.all().values_list("id", flat=True)),
                "images": list(page.related_images.all().values_list("id", flat=True)),
                "videos": list(page.related_videos.all().values_list("id", flat=True)),
            }
            page.id = uuid.uuid4()
            page.site = target_site
            page.story = story
            page.save()

            copy_related_media(page, source_media, audio_map, image_map, video_map)
            page.save()


def copy_dictionary_entries_and_return_map(
    source_site,
    target_site,
    category_map,
    character_map,
    audio_map,
    image_map,
    video_map,
):
    dictionary_entry_map = {}

    dictionary_entries = list(
        DictionaryEntry.objects.filter(site=source_site)
        .annotate(related_entry_count=Count("related_dictionary_entries"))
        .order_by("related_entry_count")
        .distinct()
    )
    for entry in dictionary_entries:
        source_categories = list(entry.categories.all())
        source_related_characters = list(entry.related_characters.all())
        source_related_entries = list(entry.related_dictionary_entries.all())
        source_media = {
            "audio": list(entry.related_audio.values_list("id", flat=True)),
            "images": list(entry.related_images.values_list("id", flat=True)),
            "videos": list(entry.related_videos.values_list("id", flat=True)),
        }

        source_entry_id = entry.id
        target_entry_id = uuid.uuid4()
        dictionary_entry_map[source_entry_id] = target_entry_id

        entry.id = target_entry_id
        entry.site = target_site
        entry.batch_id = ""
        entry.import_job = None
        entry.save()

        updated_categories = [
            category_map[category.id] for category in source_categories
        ]
        entry.categories.set(updated_categories)

        updated_related_characters = [
            character_map[char.id] for char in source_related_characters
        ]
        entry.related_characters.set(updated_related_characters)

        updated_related_entries = [
            dictionary_entry_map[source_related_entry.id]
            for source_related_entry in source_related_entries
            if source_related_entry.id in dictionary_entry_map
        ]
        entry.related_dictionary_entries.set(updated_related_entries)

        copy_related_media(entry, source_media, audio_map, image_map, video_map)
        entry.save()

    return dictionary_entry_map


def copy_immersion_labels(source_site, target_site, dictionary_entry_map):
    imm_labels = list(ImmersionLabel.objects.filter(site=source_site))
    for imm_label in imm_labels:
        imm_label.id = uuid.uuid4()
        imm_label.site = target_site

        source_dictionary_entry = imm_label.dictionary_entry
        imm_label.dictionary_entry_id = dictionary_entry_map[source_dictionary_entry.id]

        imm_label.save()


def copy_related_objects(source_site, target_site, user, logger):
    copy_site_features(source_site, target_site)
    logger.info("Site features copied.")

    category_map = copy_categories_and_return_map(source_site, target_site, user)
    logger.info("Categories copied.")

    audio_map = copy_audio_and_speakers_and_return_map(source_site, target_site, logger)
    logger.info("Audio and speakers copied.")
    image_map = copy_images_and_return_map(source_site, target_site, logger)
    logger.info("Images copied.")
    video_map = copy_videos_and_return_map(source_site, target_site, logger)
    logger.info("Videos copied.")

    character_map = copy_all_characters_and_return_map(
        source_site, target_site, audio_map, image_map, video_map
    )
    copy_alphabet(source_site, target_site)
    logger.info("Characters and alphabet copied.")

    copy_galleries(source_site, target_site, image_map, logger)
    copy_songs(source_site, target_site, audio_map, image_map, video_map)
    copy_stories(source_site, target_site, audio_map, image_map, video_map)
    logger.info("Galleries, songs and stories copied.")

    dictionary_entry_map = copy_dictionary_entries_and_return_map(
        source_site,
        target_site,
        category_map,
        character_map,
        audio_map,
        image_map,
        video_map,
    )

    copy_immersion_labels(source_site, target_site, dictionary_entry_map)
    logger.info("Dictionary entries and immersion labels copied.")


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

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)

        source_slug = options["source_slug"]
        target_slug = options["target_slug"]
        user_email = options["email"]
        force_delete = options["force_delete"]

        logger.info("Verifying requirements.")

        source_site = get_valid_object(
            Site, slug=source_slug, error="Provided source site does not exist."
        )
        user = get_valid_object(
            get_user_model(),
            email=user_email,
            error="No user found with the provided email.",
        )
        verify_target_site_does_not_exist(target_slug, force_delete)

        logger.info(
            f"Creating new site: {target_slug} and copying content from {source_slug}."
        )

        target_site = create_new_site(source_site, target_slug, user)

        copy_related_objects(source_site, target_site, user, logger)
        logger.info("Site copy completed successfully.")
