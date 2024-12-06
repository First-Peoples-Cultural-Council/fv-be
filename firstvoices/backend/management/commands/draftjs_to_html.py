import json
import logging

from django.core.management.base import BaseCommand
from draftjs_exporter.html import HTML

from backend.models import Site, Song, Story, StoryPage
from backend.models.widget import WidgetSettings


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

    def handle(self, *args, **options):
        logger = logging.getLogger("draftjs_to_html")
        logger.setLevel(logging.INFO)

        site_slug_list = options.get("site_slugs")
        if site_slug_list:
            site_slugs = site_slug_list.split(",").strip()
            sites = Site.objects.filter(slug__in=site_slugs)
        else:
            sites = Site.objects.all()

        for site in sites:
            logger.info(f"Converting draftjs content to html for site {site.slug}...")
            songs_to_convert = Song.objects.filter(site=site)
            stories_to_convert = Story.objects.filter(site=site)
            story_pages_to_convert = StoryPage.objects.filter(site=site)
            widget_settings_to_convert = WidgetSettings.objects.filter(
                site=site, key="textWithFormtting"
            )

            for song in songs_to_convert:
                logger.info(f"Converting draftjs content to html for song {song.id}...")
                song.introduction = self.convert_draftjs_to_html(song.introduction)
                song.introduction_translation = self.convert_draftjs_to_html(
                    song.introduction_translation
                )
                song.save(set_modified_date=False)

            for story in stories_to_convert:
                logger.info(
                    f"Converting draftjs content to html for story {story.id}..."
                )
                story.introduction = self.convert_draftjs_to_html(story.introduction)
                story.introduction_translation = self.convert_draftjs_to_html(
                    story.introduction_translation
                )
                story.save(set_modified_date=False)

            for story_page in story_pages_to_convert:
                logger.info(
                    f"Converting draftjs content to html for story page {story_page.id}..."
                )
                story_page.text = self.convert_draftjs_to_html(story_page.text)
                story_page.text_translation = self.convert_draftjs_to_html(
                    story_page.text_translation
                )
                story_page.save(set_modified_date=False)

            for widget_setting in widget_settings_to_convert:
                logger.info(
                    f"Converting draftjs content to html for widget setting {widget_setting.id}..."
                )
                widget_setting.value = self.convert_draftjs_to_html(
                    widget_setting.value
                )
                widget_setting.save(set_modified_date=False)

        logger.info("Conversion complete.")
