import json
import logging

from django.core.management.base import BaseCommand
from draftjs_exporter.html import HTML

from backend.models import Site, Song, Story, StoryPage
from backend.models.widget import SiteWidget, WidgetSettings


class Command(BaseCommand):
    help = "Convert fv-be draftjs content to html content."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sites",
            dest="site_slugs",
            help="Site slugs of the sites to convert draftjs content for, separated by comma (optional)",
            default=None,
        )

    @staticmethod
    def is_draftjs_content(text):
        try:
            content = json.loads(text)
            return (
                isinstance(content, dict)
                and "blocks" in content
                and "entityMap" in content
            )
        except json.JSONDecodeError:
            return False

    def convert_draftjs_to_html(self, text):
        if self.is_draftjs_content(text):
            exporter = HTML()
            return exporter.render(json.loads(text))
        return text

    def extract_entities(self, draftjs_data):
        # analyze draftjs content and extract a list of src urls for LINK, DOCUMENT, IMAGE and EMBED entities
        entity_map = draftjs_data.get("entityMap", {})
        entity_urls = []

        for entity_key, entity in entity_map.items():
            entity_type = entity.get("type")
            entity_data = entity.get("data")
            if entity_type in ["LINK", "DOCUMENT"]:
                entity_urls.append(entity_data.get("url"))
            elif entity_type in ["IMAGE", "EMBED"]:
                entity_urls.append(entity_data.get("src"))

        return entity_urls

    def process_draftjs_fields(self, instance, fields):
        # convert draftjs content in instance fields to html
        # if LINK, DOCUMENT, IMAGE or EMBED entities are present:
        # save them to the notes of the instance
        notes = instance.notes
        for field in fields:
            value = getattr(instance, field)
            if self.is_draftjs_content(value):
                draftjs_data = json.loads(value)
                entity_urls = self.extract_entities(draftjs_data)
                if entity_urls:
                    notes.extend(entity_urls)

                setattr(instance, field, self.convert_draftjs_to_html(value))
        instance.notes = notes
        instance.save(set_modified_date=False)

    def process_draftjs_widgets(self, setting):
        # convert draftjs content in widget settings to html
        # if LINK, DOCUMENT, IMAGE or EMBED entities are present:
        # warn in the logger and print there source urls if applicable
        value = setting.value
        if self.is_draftjs_content(value):
            draftjs_data = json.loads(value)
            entity_urls = self.extract_entities(draftjs_data)
            if entity_urls:
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Widget setting {setting.id} for widget {setting.widget.id} contains entities: {entity_urls}"
                    "\nPlease check to see if these URLs have content that needs to be migrated."
                )
            setting.value = self.convert_draftjs_to_html(value)
            setting.save(set_modified_date=False)

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)

        if options.get("site_slugs"):
            site_slug_list = [
                s.strip() for s in options.get("site_slugs", "").split(",")
            ]
            sites = Site.objects.filter(slug__in=site_slug_list)
            if not sites:
                logger.warning("No sites with the provided slug(s) found.")
                return
        else:
            sites = Site.objects.all()

        for site in sites:
            logger.debug(f"Converting draftjs content to html for site {site.slug}...")
            songs_to_convert = Song.objects.filter(site=site)
            stories_to_convert = Story.objects.filter(site=site)
            story_pages_to_convert = StoryPage.objects.filter(site=site)
            site_widgets = SiteWidget.objects.filter(site=site)
            widget_settings_to_convert = WidgetSettings.objects.filter(
                widget__in=site_widgets, key="textWithFormatting"
            )

            for song in songs_to_convert:
                logger.debug(
                    f"Converting draftjs content to html for song {song.id}..."
                )
                self.process_draftjs_fields(
                    song, ["introduction", "introduction_translation"]
                )

            for story in stories_to_convert:
                logger.debug(
                    f"Converting draftjs content to html for story {story.id}..."
                )
                self.process_draftjs_fields(
                    story, ["introduction", "introduction_translation"]
                )

            for story_page in story_pages_to_convert:
                logger.debug(
                    f"Converting draftjs content to html for story page {story_page.id}..."
                )
                self.process_draftjs_fields(story_page, ["text", "translation"])

            for widget_setting in widget_settings_to_convert:
                logger.debug(
                    f"Converting draftjs content to html for widget setting {widget_setting.id}..."
                )
                self.process_draftjs_widgets(widget_setting)

        logger.info("Conversion complete.")
