import logging
import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from backend.models.category import Category
from backend.models.characters import (
    Alphabet,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from backend.models.media import Audio
from backend.models.sites import Site, SiteFeature, SiteMenu


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
        # title = options["title"]

        logger.info("Verifying requirements.")
        # Verify if the original site exists
        # todo: Read more about django's exceptions and maybe find a more appropriate for here
        source_site = Site.objects.filter(slug=source_slug)
        if len(source_site) == 0:
            raise ValidationError(
                "Provided source site does not exist. Please verify and try again."
            )
        source_site = source_site[0]

        # Verify the target site does not exist
        if Site.objects.filter(slug=target_slug).exists():
            raise ValidationError(
                f"Site with slug {target_slug} already exists. Please use a different target slug."
            )

        # Verify if user exists with the provided email
        users = get_user_model().objects.filter(email=user_email)
        if len(users) == 0:
            raise ValidationError("No user found with the provided email.")
        user = users[0]

        logger.info(
            f"Looks good. Creating a new site and copying all content from {source_slug} to {target_slug}."
        )

        # Create a new site
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

        # Memberships ?
        # JoinRequest & JoinRequestReason ?

        # SiteFeature
        site_features = SiteFeature.objects.filter(site=source_site)
        for site_feature in site_features:
            site_feature.id = uuid.uuid4()
            site_feature.site = new_site
            site_feature.save()

        # SiteMenu
        site_menu_list = SiteMenu.objects.filter(site=source_site)
        for site_menu in site_menu_list:
            site_menu.id = uuid.uuid4()
            site_menu.site = new_site
            site_menu.save()

        # Character and variants
        characters = Character.objects.filter(site=source_site)
        for character in characters:
            variants = CharacterVariant.objects.filter(base_character=character)

            character.id = uuid.uuid4()
            character.site = new_site
            character.save()

            # Variants
            for variant in variants:
                variant.id = uuid.uuid4()
                variant.site = new_site
                variant.base_character = character
                variant.save()

        # IgnoredCharacter
        ignored_characters = IgnoredCharacter.objects.filter(site=source_site)
        for ignored_character in ignored_characters:
            ignored_character.id = uuid.uuid4()
            ignored_character.site = new_site
            ignored_character.save()

        # Alphabet
        alphabets = Alphabet.objects.filter(site=source_site)
        for alphabet in alphabets:
            alphabet.id = uuid.uuid4()
            alphabet.site = new_site
            alphabet.save()

        # Category
        # Removing auto-generated categories
        Category.objects.filter(site=new_site).delete()
        # Copy over all the parent categories
        categories = Category.objects.filter(
            site=source_site, children__isnull=False
        ).distinct()
        for category in categories:
            child_categories = category.children.all()

            category.id = uuid.uuid4()
            category.site = new_site
            category.save()

            for child_category in child_categories:
                child_category.id = uuid.uuid4()
                child_category.site = new_site
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
            category.id = uuid.uuid4()
            category.site = new_site
            category.save()

        # Person
        # person_list = Person.objects.filter(site=source_site)
        # for person in person_list:
        #     person.id = uuid.uuid4()
        #     person.site = new_site
        #     person.save()

        # Audio
        audio_files = Audio.objects.filter(site=source_site)
        for audio_file in audio_files:
            # speakers need to be updated
            current_speakers = audio_file.speakers.all()

            for person in current_speakers:
                person.id = uuid.uuid4()
                person.site = new_site
                person.save()
                audio_file.speakers

            # original needs to be updated

        # Copy over rest of the persons which are not linked to any audio file

        # List of stuff to be generated and/or copied over.
        """
            Required
            - Widget, WidgetSettings, SiteWidgetList, SiteWidgetListOrder
            - SitePage
            - Audio, AudioSpeaker
            - File
            - Image, Video, Generate thumbnails, RelatedMediaMixin
            - Gallery, GalleryItem
            - Song, Lyric
            - Story, StoryPage

            - DictionaryEntry, DictionaryEntryLink, DictionaryEntryRelatedCharacter, DictionaryEntryCategory
            - ImmersionLabel

            Probably not required:
            - WordOfTheDay
            - ImportJobs

            Misc. Stuff
            - Language
            - LanguageFamily
        """

        # Index the site and all the copied over stuff

        logger.info("All done.")
