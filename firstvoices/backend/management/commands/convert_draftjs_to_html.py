import json
import logging

from django.core.management.base import BaseCommand
from draftjs_exporter.defaults import BLOCK_MAP, STYLE_MAP
from draftjs_exporter.html import HTML

from backend.models import Site, Song, Story, StoryPage
from backend.models.widget import SiteWidget, WidgetSettings

DRAFTJS_EXPORTER_CONFIG = {
    "block_map": BLOCK_MAP,
    "style_map": STYLE_MAP,
    "entity_decorators": {
        "FALLBACK": lambda props: props.get("children", ""),
    },
    "composite_decorators": [],
}


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

    @staticmethod
    def log_entity(entity_map):
        logger = logging.getLogger(__name__)

        entity = entity_map["0"]
        logger.debug("Ignored entity with the following info:")
        logger.debug(f"Entity type: {entity['type']}")
        logger.debug(f"Entity data: {entity['data']}")

    def convert_draftjs_to_html(self, text):
        if self.is_draftjs_content(text):
            exporter = HTML(DRAFTJS_EXPORTER_CONFIG)
            draftjs_data = json.loads(text)
            if draftjs_data["entityMap"]:
                self.log_entity(draftjs_data["entityMap"])
            return exporter.render(json.loads(text))
        return text

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
                song.introduction = self.convert_draftjs_to_html(song.introduction)
                song.introduction_translation = self.convert_draftjs_to_html(
                    song.introduction_translation
                )
                song.save(set_modified_date=False)

            for story in stories_to_convert:
                logger.debug(
                    f"Converting draftjs content to html for story {story.id}..."
                )
                story.introduction = self.convert_draftjs_to_html(story.introduction)
                story.introduction_translation = self.convert_draftjs_to_html(
                    story.introduction_translation
                )
                story.save(set_modified_date=False)

            for story_page in story_pages_to_convert:
                logger.debug(
                    f"Converting draftjs content to html for story page {story_page.id}..."
                )
                story_page.text = self.convert_draftjs_to_html(story_page.text)
                story_page.translation = self.convert_draftjs_to_html(
                    story_page.translation
                )
                story_page.save(set_modified_date=False)

            for widget_setting in widget_settings_to_convert:
                logger.debug(
                    f"Converting draftjs content to html for widget setting {widget_setting.id}..."
                )
                widget_setting.value = self.convert_draftjs_to_html(
                    widget_setting.value
                )
                widget_setting.save(set_modified_date=False)

        logger.info("Conversion complete.")
