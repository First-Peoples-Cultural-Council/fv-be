import pytest

from backend.management.commands import convert_lyrics_draftjs_to_text
from backend.models import Lyric
from backend.tests import factories


class TestConvertLyricsDraftjsToText:
    @pytest.mark.django_db
    def test_lyric_text(self):
        existing_text = """{
                          "entityMap": {},
                          "blocks": [
                            {
                              "key": "",
                              "text": "test line one",
                              "type": "unstyled",
                              "depth": 0,
                              "inlineStyleRanges": [],
                              "entityRanges": [],
                              "data": {}
                            },
                            {
                              "key": "",
                              "text": "test line two",
                              "type": "unstyled",
                              "depth": 0,
                              "inlineStyleRanges": [],
                              "entityRanges": [],
                              "data": {}
                            }
                          ]
                        }"""
        factories.LyricsFactory.create(text=existing_text)

        assert Lyric.objects.count() == 1

        convert_lyrics_draftjs_to_text.lyric_draftjs_to_text()

        assert Lyric.objects.count() == 1
        assert Lyric.objects.first().text == "test line one\ntest line two"

    @pytest.mark.django_db
    def test_lyric_translation(self):
        existing_translation = """{
                  "entityMap": {},
                  "blocks": [
                    {
                      "key": "",
                      "text": "test line one",
                      "type": "unstyled",
                      "depth": 0,
                      "inlineStyleRanges": [],
                      "entityRanges": [],
                      "data": {}
                    },
                    {
                      "key": "",
                      "text": "test line two",
                      "type": "unstyled",
                      "depth": 0,
                      "inlineStyleRanges": [],
                      "entityRanges": [],
                      "data": {}
                    }
                  ]
                }"""
        factories.LyricsFactory.create(translation=existing_translation)

        assert Lyric.objects.count() == 1

        convert_lyrics_draftjs_to_text.lyric_draftjs_to_text()

        assert Lyric.objects.count() == 1
        assert Lyric.objects.first().translation == "test line one\ntest line two"

    @pytest.mark.django_db
    def test_lyric_unchanged(self):
        existing_text = "already plain text"
        factories.LyricsFactory.create(text=existing_text)

        assert Lyric.objects.count() == 1

        convert_lyrics_draftjs_to_text.lyric_draftjs_to_text()

        assert Lyric.objects.count() == 1
        assert Lyric.objects.first().text == existing_text

    @pytest.mark.django_db
    def test_lyric_missing_blocks(self):
        existing_text = """{
                  "entityMap": {}
                }"""
        factories.LyricsFactory.create(text=existing_text)

        assert Lyric.objects.count() == 1

        convert_lyrics_draftjs_to_text.lyric_draftjs_to_text()

        assert Lyric.objects.count() == 1
        assert Lyric.objects.first().text == existing_text
