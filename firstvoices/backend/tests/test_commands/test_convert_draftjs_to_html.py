import json
import logging

import pytest
from django.core.management import call_command

from backend.tests import factories


class TestConvertDraftjsToHtml:
    @staticmethod
    def make_draftjs_content(text):
        draftjs_data = {
            "blocks": [
                {
                    "key": "1",
                    "text": text,
                    "type": "unstyled",
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                    "data": {},
                }
            ],
            "entityMap": {},
        }
        return json.dumps(draftjs_data)

    @staticmethod
    def make_draftjs_content_with_entity(text, entity_type, entity_data):
        draftjs_data = {
            "blocks": [
                {
                    "key": "1",
                    "text": text,
                    "type": "unstyled",
                    "depth": 0,
                    "inlineStyleRanges": [],
                    "entityRanges": [],
                    "data": {},
                }
            ],
            "entityMap": {
                "0": {
                    "type": entity_type,
                    "mutability": "MUTABLE",
                    "data": entity_data,
                }
            },
        }
        return json.dumps(draftjs_data)

    @pytest.mark.django_db
    def test_convert_draftjs_to_html_invalid_sites(self, caplog):
        call_command("convert_draftjs_to_html", site_slugs="invalid-site")
        assert "No sites with the provided slug(s) found." in caplog.text

    @pytest.mark.django_db
    def test_convert_draftjs_to_html_no_draftjs_content(self, caplog):
        site = factories.SiteFactory.create()

        song = factories.SongFactory.create(site=site)
        song.introduction = "Song introduction"
        song.introduction_translation = "Translated song introduction"
        song.save()

        story = factories.StoryFactory.create(site=site)
        story.introduction = "Story introduction"
        story.introduction_translation = "Translated story introduction"
        story.save()

        story_page = factories.StoryPageFactory.create(story=story)
        story_page.text = "Story page text"
        story_page.translation = "Translated story page text"
        story_page.save()

        widget = factories.SiteWidgetFactory.create(site=site)
        widget_setting = factories.WidgetSettingsFactory.create(
            widget=widget, key="textWithFormatting"
        )
        widget_setting.value = "Widget setting value"
        widget_setting.save()

        call_command("convert_draftjs_to_html", site_slugs=site.slug)

        song.refresh_from_db()
        story.refresh_from_db()
        story_page.refresh_from_db()
        widget_setting.refresh_from_db()

        assert song.introduction == "Song introduction"
        assert song.introduction_translation == "Translated song introduction"
        assert story.introduction == "Story introduction"
        assert story.introduction_translation == "Translated story introduction"
        assert story_page.text == "Story page text"
        assert story_page.translation == "Translated story page text"
        assert widget_setting.value == "Widget setting value"

    @pytest.mark.django_db
    def test_convert_draftjs_to_html_single_site(self, caplog):
        site = factories.SiteFactory.create()

        song = factories.SongFactory.create(site=site)
        song.introduction = self.make_draftjs_content("Song introduction")
        song.introduction_translation = self.make_draftjs_content(
            "Translated song introduction"
        )
        song.save()
        song_last_modified = song.last_modified
        song_system_last_modified = song.system_last_modified

        story = factories.StoryFactory.create(site=site)
        story.introduction = self.make_draftjs_content("Story introduction")
        story.introduction_translation = self.make_draftjs_content(
            "Translated story introduction"
        )
        story.save()
        story_last_modified = story.last_modified
        story_system_last_modified = story.system_last_modified

        story_page = factories.StoryPageFactory.create(story=story)
        story_page.text = self.make_draftjs_content("Story page text")
        story_page.translation = self.make_draftjs_content("Translated story page text")
        story_page.save()
        story_page_last_modified = story_page.last_modified
        story_page_system_last_modified = story_page.system_last_modified

        widget = factories.SiteWidgetFactory.create(site=site)
        widget_setting = factories.WidgetSettingsFactory.create(
            widget=widget, key="textWithFormatting"
        )
        widget_setting.value = self.make_draftjs_content("Widget setting value")
        widget_setting.save()
        widget_setting_last_modified = widget_setting.last_modified
        widget_setting_system_last_modified = widget_setting.system_last_modified

        call_command("convert_draftjs_to_html", site_slugs=site.slug)

        song.refresh_from_db()
        story.refresh_from_db()
        story_page.refresh_from_db()
        widget_setting.refresh_from_db()

        assert song.introduction == "<p>Song introduction</p>"
        assert song.introduction_translation == "<p>Translated song introduction</p>"
        assert story.introduction == "<p>Story introduction</p>"
        assert story.introduction_translation == "<p>Translated story introduction</p>"
        assert story_page.text == "<p>Story page text</p>"
        assert story_page.translation == "<p>Translated story page text</p>"
        assert widget_setting.value == "<p>Widget setting value</p>"

        assert song.last_modified == song_last_modified
        assert story.last_modified == story_last_modified
        assert story_page.last_modified == story_page_last_modified
        assert widget_setting.last_modified == widget_setting_last_modified

        assert song.system_last_modified > song_system_last_modified
        assert story.system_last_modified > story_system_last_modified
        assert story_page.system_last_modified > story_page_system_last_modified
        assert widget_setting.system_last_modified > widget_setting_system_last_modified

        assert "Conversion complete." in caplog.text

    @pytest.mark.django_db
    def test_convert_draftjs_to_html_multi_site(self, caplog):
        site1 = factories.SiteFactory.create()
        site2 = factories.SiteFactory.create()

        song1 = factories.SongFactory.create(site=site1)
        song1.introduction = self.make_draftjs_content("Song introduction")
        song1.introduction_translation = self.make_draftjs_content(
            "Translated song introduction"
        )
        song1.save()

        song2 = factories.SongFactory.create(site=site2)
        song2.introduction = self.make_draftjs_content("Song introduction")
        song2.introduction_translation = self.make_draftjs_content(
            "Translated song introduction"
        )
        song2.save()

        call_command("convert_draftjs_to_html")

        song1.refresh_from_db()
        song2.refresh_from_db()

        assert song1.introduction == "<p>Song introduction</p>"
        assert song1.introduction_translation == "<p>Translated song introduction</p>"
        assert song2.introduction == "<p>Song introduction</p>"
        assert song2.introduction_translation == "<p>Translated song introduction</p>"

        assert "Conversion complete." in caplog.text

    @pytest.mark.django_db
    def test_convert_draftjs_to_html_with_entities_logged(self, caplog):
        caplog.set_level(logging.DEBUG)
        site = factories.SiteFactory.create()

        song = factories.SongFactory.create(site=site)
        song.introduction = self.make_draftjs_content_with_entity(
            "Song introduction",
            "LINK",
            {"url": "https://www.firstvoices.com"},
        )
        song.introduction_translation = self.make_draftjs_content_with_entity(
            "Translated song introduction",
            "IMAGE",
            {"src": "https://www.firstvoices.com/image.jpg"},
        )
        song.save()

        call_command("convert_draftjs_to_html", site_slugs=site.slug)

        song.refresh_from_db()

        assert song.introduction == "<p>Song introduction</p>"
        assert song.introduction_translation == "<p>Translated song introduction</p>"

        assert (
            f"Converting draftjs content to html for site {site.slug}..." in caplog.text
        )
        assert (
            f"Converting draftjs content to html for song {song.id}..." in caplog.text
        )

        assert "Ignored entity with the following info:" in caplog.text
        assert "Entity type: LINK" in caplog.text
        assert "Entity data: {'url': 'https://www.firstvoices.com'}" in caplog.text

        assert "Entity type: IMAGE" in caplog.text
        assert (
            "Entity data: {'src': 'https://www.firstvoices.com/image.jpg'}"
            in caplog.text
        )

        assert "Conversion complete." in caplog.text
        assert "draftjs_exporter.error.ConfigException" not in caplog.text
