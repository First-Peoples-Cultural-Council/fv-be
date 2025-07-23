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
from backend.models.song import Lyric, Song
from backend.models.story import Story, StoryPage


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


def copy_site_features(source_site, target_site, set_modified_date):
    site_features = list(SiteFeature.objects.filter(site=source_site))
    for site_feature in site_features:
        site_feature.id = uuid.uuid4()
        site_feature.site = target_site
        site_feature.save(set_modified_date=set_modified_date)


def copy_all_characters_and_return_map(
    source_site, target_site, audio_map, image_map, video_map, set_modified_date
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
        character.save(set_modified_date=set_modified_date)

        copy_related_media(
            character, source_media, audio_map, image_map, video_map, set_modified_date
        )

    variants = list(CharacterVariant.objects.filter(site=source_site))
    for variant in variants:
        source_base_character = variant.base_character

        variant.id = uuid.uuid4()
        variant.site = target_site
        variant.base_character_id = character_map[source_base_character.id]
        variant.save(set_modified_date=set_modified_date)

    ignored_characters = list(IgnoredCharacter.objects.filter(site=source_site))
    for ignored_character in ignored_characters:
        ignored_character.id = uuid.uuid4()
        ignored_character.site = target_site
        ignored_character.save(set_modified_date=set_modified_date)

    return character_map


def copy_alphabet(source_site, target_site, set_modified_date):
    alphabets = list(Alphabet.objects.filter(site=source_site))
    for alphabet in alphabets:
        alphabet.id = uuid.uuid4()
        alphabet.site = target_site
        alphabet.save(set_modified_date=set_modified_date)


def copy_categories_and_return_map(source_site, target_site, user, set_modified_date):
    category_map = {}

    # Removing auto-generated categories
    Category.objects.filter(site=target_site).delete()

    # Copying over parent categories first, then rest
    categories = list(
        Category.objects.filter(site=source_site)
        .annotate(children_count=Count("children"))
        .order_by("-children_count")
        .distinct()
    )
    for category in categories:
        current_parent_id = category.parent.id if category.parent else None
        source_category_id = category.id
        target_category_id = uuid.uuid4()
        category_map[source_category_id] = target_category_id

        category.id = target_category_id
        category.site = target_site
        category.created_by = user
        category.last_modified_by = user

        if current_parent_id:
            category.parent_id = category_map[current_parent_id]

        category.save(set_modified_date=set_modified_date)

    return category_map


def copy_speakers_and_return_map(source_site, target_site, set_modified_date):
    speaker_map = {}
    source_speakers = list(Person.objects.filter(site=source_site))
    for speaker in source_speakers:
        source_speaker_id = speaker.id
        target_speaker_id = uuid.uuid4()
        speaker_map[source_speaker_id] = target_speaker_id

        speaker.id = target_speaker_id
        speaker.site = target_site
        speaker.save(set_modified_date=set_modified_date)

    return speaker_map


def copy_audio_and_speakers_and_return_map(
    source_site, target_site, speaker_map, set_modified_date, logger
):
    audio_map = {}

    audio_instances = list(Audio.objects.filter(site=source_site))
    for audio in audio_instances:
        try:
            target_file = File(
                content=UploadedFile(audio.original.content.file),
                site=target_site,
            )
            target_file.save()
            audio.original = target_file

            # Speakers
            current_speakers = list(audio.speakers.all())

            audio.site = target_site
            source_audio_id = audio.id
            target_audio_id = uuid.uuid4()
            audio_map[source_audio_id] = target_audio_id

            audio.id = target_audio_id
            # To skip conditionals in the base media models and copy audio instance
            audio._state.adding = True
            audio.save(set_modified_date=set_modified_date)

            updated_speakers = [speaker_map[speaker.id] for speaker in current_speakers]
            audio.speakers.set(updated_speakers)
        except Exception as e:
            logger.warning(f"Couldn't copy audio file with id: {audio.id}", exc_info=e)

    return audio_map


def copy_images_and_return_map(source_site, target_site, set_modified_date, logger):
    image_map = {}

    images = list(Image.objects.filter(site=source_site))
    for image in images:
        try:
            # Content
            target_file = ImageFile(
                content=UploadedFile(image.original.content.file),
                site=target_site,
            )
            target_file.save()
            image.original = target_file

            image.thumbnail = None
            image.small = None
            image.medium = None
            image.site = target_site

            source_img_id = image.id
            target_img_id = uuid.uuid4()
            image_map[source_img_id] = target_img_id

            image.id = target_img_id
            # To skip conditionals in the base media models and copy image instance
            image._state.adding = True
            image.save(set_modified_date=set_modified_date)
        except Exception as e:
            logger.warning(f"Couldn't copy image file with id: {image.id}", exc_info=e)

    return image_map


def copy_videos_and_return_map(source_site, target_site, set_modified_date, logger):
    video_map = {}

    videos = list(Video.objects.filter(site=source_site))
    for video in videos:
        try:
            # Content
            target_file = VideoFile(
                content=UploadedFile(video.original.content.file),
                site=target_site,
            )
            target_file.save()
            video.original = target_file

            video.thumbnail = None
            video.small = None
            video.medium = None
            video.site = target_site

            source_video_id = video.id
            target_video_id = uuid.uuid4()
            video_map[source_video_id] = target_video_id

            video.id = target_video_id
            # To skip conditionals in the base media models and copy video instance
            video._state.adding = True
            video.save(set_modified_date=set_modified_date)
        except Exception as e:
            logger.warning(f"Couldn't copy video file with id: {video.id}", exc_info=e)

    return video_map


def copy_galleries(source_site, target_site, image_map, set_modified_date, logger):
    galleries = list(Gallery.objects.filter(site=source_site))

    shared_media_sites_ids = list(
        SiteFeature.objects.filter(
            key__iexact="shared_media", is_enabled=True
        ).values_list("site", flat=True)
    )
    shared_images_library = list(
        Image.objects.filter(site__id__in=shared_media_sites_ids).values_list(flat=True)
    )

    for gallery in galleries:
        gallery_items = list(gallery.galleryitem_set.all())
        source_cover_img_id = gallery.cover_image.id if gallery.cover_image else None

        gallery.site = target_site

        if source_cover_img_id:
            new_cover_img_id = get_target_image_id(
                source_cover_img_id, image_map, shared_images_library
            )
            if new_cover_img_id:
                gallery.cover_image_id = new_cover_img_id
            else:
                logger.warning(
                    f"Gallery.cover_image is not present in image map. Gallery Id: {gallery.id}."
                )

        gallery.id = uuid.uuid4()
        gallery.save(set_modified_date=set_modified_date)

        updated_gallery_items = []
        for gallery_item in gallery_items:
            target_img_id = get_target_image_id(
                gallery_item.image.id, image_map, shared_images_library
            )
            if not target_img_id:
                logger.warning(
                    f"Missing gallery_item.image in image map with id: {gallery_item.image.id}."
                )
                continue

            new_gallery_item = GalleryItem(
                gallery=gallery,
                image_id=target_img_id,
                ordering=gallery_item.ordering,
            )
            new_gallery_item.save()
            updated_gallery_items.append(new_gallery_item)

        gallery.galleryitem_set.set(updated_gallery_items)


def get_target_image_id(source_image_id, image_map, shared_images_library):
    # helper method to get image id if its present in the image_map, or in the shared images library
    if source_image_id in shared_images_library:
        return source_image_id
    elif source_image_id in image_map:
        return image_map[source_image_id]
    return None


def copy_related_media(
    instance, source_media, audio_map, image_map, video_map, set_modified_date
):
    # If the media is missing the original, that media file is not copied, and thus
    # also not added to the m2m for an instance
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

    # If the image is present in the shared image library, refer to it directly
    shared_media_sites_ids = list(
        SiteFeature.objects.filter(
            key__iexact="shared_media", is_enabled=True
        ).values_list("site", flat=True)
    )
    shared_images_library = list(
        Image.objects.filter(site__id__in=shared_media_sites_ids).values_list(flat=True)
    )

    # If the image is present in the shared image library, refer to it directly
    target_images = []
    for image_id in source_media["images"]:
        target_image_id = get_target_image_id(
            image_id, image_map, shared_images_library
        )
        if target_image_id:
            target_images.append(target_image_id)

    if target_images:
        instance.related_images.set(target_images)
    if target_videos:
        instance.related_videos.set(target_videos)
    if target_audio:
        instance.related_audio.set(target_audio)
    instance.save(set_modified_date=set_modified_date)


def copy_songs(
    source_site, target_site, audio_map, image_map, video_map, set_modified_date
):
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
        song.save(set_modified_date=set_modified_date)

        for lyric in source_lyrics:
            lyric.id = uuid.uuid4()
            lyric.song = song
            lyric.save(set_modified_date=set_modified_date)

        copy_related_media(
            song, source_media, audio_map, image_map, video_map, set_modified_date
        )


def copy_stories(
    source_site, target_site, audio_map, image_map, video_map, set_modified_date
):
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
        story.save(set_modified_date=set_modified_date)

        copy_related_media(
            story, source_media, audio_map, image_map, video_map, set_modified_date
        )

        for page in source_pages:
            source_media = {
                "audio": list(page.related_audio.all().values_list("id", flat=True)),
                "images": list(page.related_images.all().values_list("id", flat=True)),
                "videos": list(page.related_videos.all().values_list("id", flat=True)),
            }
            page.id = uuid.uuid4()
            page.site = target_site
            page.story = story
            page.save(set_modified_date=set_modified_date)

            copy_related_media(
                page, source_media, audio_map, image_map, video_map, set_modified_date
            )


def copy_dictionary_entries_and_return_map(
    source_site,
    target_site,
    category_map,
    character_map,
    audio_map,
    image_map,
    video_map,
    set_modified_date,
):
    dictionary_entry_map = {}

    dictionary_entries = list(DictionaryEntry.objects.filter(site=source_site))
    # First pass to create new entries and fill up the map
    for entry in dictionary_entries:
        source_entry_id = entry.id
        target_entry_id = uuid.uuid4()
        dictionary_entry_map[source_entry_id] = target_entry_id

        entry.id = target_entry_id
        entry.site = target_site
        entry.legacy_batch_filename = ""
        entry.import_job = None
        entry.save(set_modified_date=set_modified_date)

    dictionary_entries = list(DictionaryEntry.objects.filter(site=source_site))
    # Second pass to set all the relationships
    for source_entry in dictionary_entries:
        target_entry_id = dictionary_entry_map[source_entry.id]
        target_entry = DictionaryEntry.objects.get(id=target_entry_id)

        source_categories = list(source_entry.categories.all())
        updated_categories = [
            category_map[category.id] for category in source_categories
        ]
        target_entry.categories.set(updated_categories)

        source_related_characters = list(source_entry.related_characters.all())
        updated_related_characters = [
            character_map[char.id] for char in source_related_characters
        ]
        target_entry.related_characters.set(updated_related_characters)

        source_related_entries = list(source_entry.related_dictionary_entries.all())
        updated_related_entries = [
            dictionary_entry_map[source_related_entry.id]
            for source_related_entry in source_related_entries
            if source_related_entry.id in dictionary_entry_map
        ]
        target_entry.related_dictionary_entries.set(updated_related_entries)

        source_media = {
            "audio": list(source_entry.related_audio.values_list("id", flat=True)),
            "images": list(source_entry.related_images.values_list("id", flat=True)),
            "videos": list(source_entry.related_videos.values_list("id", flat=True)),
        }
        copy_related_media(
            target_entry,
            source_media,
            audio_map,
            image_map,
            video_map,
            set_modified_date,
        )

    return dictionary_entry_map


def copy_immersion_labels(
    source_site, target_site, dictionary_entry_map, set_modified_date
):
    imm_labels = list(ImmersionLabel.objects.filter(site=source_site))
    for imm_label in imm_labels:
        imm_label.id = uuid.uuid4()
        imm_label.site = target_site

        source_dictionary_entry = imm_label.dictionary_entry
        if source_dictionary_entry:
            imm_label.dictionary_entry_id = dictionary_entry_map[
                source_dictionary_entry.id
            ]

        imm_label.save(set_modified_date=set_modified_date)


def copy_related_objects(
    source_site, target_site, user, set_modified_date, print_counts, logger
):
    copy_site_features(source_site, target_site, set_modified_date)
    logger.info("Site features copied.")

    category_map = copy_categories_and_return_map(
        source_site, target_site, user, set_modified_date
    )
    logger.info("Categories copied.")

    speaker_map = copy_speakers_and_return_map(
        source_site, target_site, set_modified_date
    )
    logger.info("Speakers copied.")

    audio_map = copy_audio_and_speakers_and_return_map(
        source_site, target_site, speaker_map, set_modified_date, logger
    )
    logger.info("Audio and speakers copied.")
    image_map = copy_images_and_return_map(
        source_site, target_site, set_modified_date, logger
    )
    logger.info("Images copied.")
    video_map = copy_videos_and_return_map(
        source_site, target_site, set_modified_date, logger
    )
    logger.info("Videos copied.")

    character_map = copy_all_characters_and_return_map(
        source_site, target_site, audio_map, image_map, video_map, set_modified_date
    )
    copy_alphabet(source_site, target_site, set_modified_date)
    logger.info("Characters and alphabet copied.")

    copy_galleries(source_site, target_site, image_map, set_modified_date, logger)
    copy_songs(
        source_site, target_site, audio_map, image_map, video_map, set_modified_date
    )
    copy_stories(
        source_site, target_site, audio_map, image_map, video_map, set_modified_date
    )
    logger.info("Galleries, songs and stories copied.")

    dictionary_entry_map = copy_dictionary_entries_and_return_map(
        source_site,
        target_site,
        category_map,
        character_map,
        audio_map,
        image_map,
        video_map,
        set_modified_date,
    )

    copy_immersion_labels(
        source_site, target_site, dictionary_entry_map, set_modified_date
    )
    logger.info("Dictionary entries and immersion labels copied.")

    if print_counts:
        log_objects_count(
            source_site,
            target_site,
            category_map,
            speaker_map,
            audio_map,
            image_map,
            video_map,
            character_map,
            dictionary_entry_map,
            logger,
        )


def log_objects_count(
    source_site,
    target_site,
    category_map,
    speaker_map,
    audio_map,
    image_map,
    video_map,
    character_map,
    dictionary_entry_map,
    logger,
):
    # Method to log count of all objects present in the source site, and in the target site
    source_site_feature_count = SiteFeature.objects.filter(site=source_site).count()
    target_site_feature_count = SiteFeature.objects.filter(site=target_site).count()
    logger.info(
        f"Site feature count:: source: {source_site_feature_count}, target: {target_site_feature_count}"
    )

    source_category_count = Category.objects.filter(site=source_site).count()
    target_category_count = Category.objects.filter(site=target_site).count()
    logger.info(
        f"Category count:: source: {source_category_count}, target: {target_category_count}, map: {len(category_map)}"
    )

    source_speakers_count = Person.objects.filter(site=source_site).count()
    target_speakers_count = Person.objects.filter(site=target_site).count()
    logger.info(
        f"Speakers count:: source: {source_speakers_count}, target: {target_speakers_count}, map: {len(speaker_map)}"
    )

    source_audio_count = Audio.objects.filter(site=source_site).count()
    target_audio_count = Audio.objects.filter(site=target_site).count()
    logger.info(
        f"Audio count:: source: {source_audio_count}, target: {target_audio_count}, map: {len(audio_map)}"
    )

    source_image_count = Image.objects.filter(site=source_site).count()
    target_image_count = Image.objects.filter(site=target_site).count()
    logger.info(
        f"Image count:: source: {source_image_count}, target: {target_image_count}, map: {len(image_map)}"
    )

    source_video_count = Video.objects.filter(site=source_site).count()
    target_video_count = Video.objects.filter(site=target_site).count()
    logger.info(
        f"Video count:: source: {source_video_count}, target: {target_video_count}, map: {len(video_map)}"
    )

    source_char_count = Character.objects.filter(site=source_site).count()
    target_char_count = Character.objects.filter(site=target_site).count()
    logger.info(
        f"Character count:: source: {source_char_count}, target: {target_char_count}, map: {len(character_map)}"
    )

    source_alphabet_count = Alphabet.objects.filter(site=source_site).count()
    target_alphabet_count = Alphabet.objects.filter(site=target_site).count()
    logger.info(
        f"Alphabet count:: source: {source_alphabet_count}, target: {target_alphabet_count}"
    )

    source_gallery_count = Gallery.objects.filter(site=source_site).count()
    target_gallery_count = Gallery.objects.filter(site=target_site).count()
    logger.info(
        f"Gallery count:: source: {source_gallery_count}, target: {target_gallery_count}"
    )
    source_gallery_item_count = GalleryItem.objects.filter(
        gallery__site=source_site
    ).count()
    target_gallery_item_count = GalleryItem.objects.filter(
        gallery__site=target_site
    ).count()
    logger.info(
        f"GalleryItem count:: source: {source_gallery_item_count}, target: {target_gallery_item_count}"
    )

    source_song_count = Song.objects.filter(site=source_site).count()
    target_song_count = Song.objects.filter(site=target_site).count()
    logger.info(
        f"Song count:: source: {source_song_count}, target: {target_song_count}"
    )
    source_song_lyrics_count = Lyric.objects.filter(song__site=source_site).count()
    target_song_lyrics_count = Lyric.objects.filter(song__site=target_site).count()
    logger.info(
        f"SongLyrics count:: source: {source_song_lyrics_count}, target: {target_song_lyrics_count}"
    )

    source_story_count = Story.objects.filter(site=source_site).count()
    target_story_count = Story.objects.filter(site=target_site).count()
    logger.info(
        f"Story count:: source: {source_story_count}, target: {target_story_count}"
    )
    source_story_pages_count = StoryPage.objects.filter(site=source_site).count()
    target_story_pages_count = StoryPage.objects.filter(site=target_site).count()
    logger.info(
        f"StoryPages count:: source: {source_story_pages_count}, target: {target_story_pages_count}"
    )

    source_dictionary_entry_count = DictionaryEntry.objects.filter(
        site=source_site
    ).count()
    target_dictionary_entry_count = DictionaryEntry.objects.filter(
        site=target_site
    ).count()
    logger.info(
        f"DictionaryEntry count:: source: {source_dictionary_entry_count}, "
        f"target: {target_dictionary_entry_count}, map: {len(dictionary_entry_map)}"
    )

    source_immersion_labels_count = ImmersionLabel.objects.filter(
        site=source_site
    ).count()
    target_immersion_labels_count = ImmersionLabel.objects.filter(
        site=target_site
    ).count()
    logger.info(
        f"ImmersionLabels count:: source: {source_immersion_labels_count}, target: {target_immersion_labels_count}"
    )


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
            "--reset-last-modified",
            dest="reset_last_modified",
            help="Reset the date-time in last_modified field of all new instances being created.",
            action="store_true",
        )
        parser.add_argument(
            "--force-delete",
            dest="force_delete",
            help="Delete target site if exists.",
            action="store_true",
        )
        parser.add_argument(
            "--print-counts",
            dest="print_counts",
            help="Helpful for debugging. Prints counts of all model instances that were copied in the "
            "format: source, target, and map(if present) .",
            action="store_true",
        )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)

        source_slug = options["source_slug"]
        target_slug = options["target_slug"]
        user_email = options["email"]
        set_modified_date = options["reset_last_modified"]
        force_delete = options["force_delete"]
        print_counts = options["print_counts"]

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

        copy_related_objects(
            source_site, target_site, user, set_modified_date, print_counts, logger
        )
        logger.info("Site copy completed successfully.")
