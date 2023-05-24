import pytest

from backend.tasks.alphabet_tasks import (
    recalculate_custom_order,
    recalculate_custom_order_preview,
)
from backend.tests import factories


class TestAlphabetTasks:
    CONFUSABLE_CUSTOM_ORDER = "⚑ᐱ⚑ᐱ⚑ᐱ"

    @pytest.fixture
    def site(self):
        return factories.SiteFactory.create(slug="test")

    @pytest.fixture
    def alphabet(self, site):
        return factories.AlphabetFactory.create(site=site)

    @pytest.mark.django_db
    def test_recalulate_preview_empty(self, site, alphabet):
        result = recalculate_custom_order_preview(site.slug)

        assert result == {"unknown_character_count": {}, "updated_entries": []}

    @pytest.mark.django_db
    def test_recalulate_preview_unknown_only(self, site, alphabet):
        factories.DictionaryEntryFactory.create(site=site, title="abc")

        result = recalculate_custom_order_preview("test")
        assert result == {
            "unknown_character_count": {"⚑a": 1, "⚑b": 1, "⚑c": 1},
            "updated_entries": [],
        }

    @pytest.mark.django_db
    def test_recalulate_preview_updated_only(self, site, alphabet):
        factories.DictionaryEntryFactory.create(site=site, title="abc")
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")

        result = recalculate_custom_order_preview("test")
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [
                {
                    "title": "abc",
                    "cleaned_title": "abc",
                    "new_custom_order": "!#$",
                    "previous_custom_order": "⚑a⚑b⚑c",
                }
            ],
        }

    @pytest.mark.django_db
    def test_recalulate_preview_confusables_only(self, site, alphabet):
        factories.CharacterFactory.create(site=site, title="A")
        factories.DictionaryEntryFactory.create(site=site, title="ᐱᐱᐱ")
        alphabet.input_to_canonical_map = [{"in": "ᐱ", "out": "A"}]
        alphabet.save()

        result = recalculate_custom_order_preview("test")
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [
                {
                    "title": "ᐱᐱᐱ",
                    "cleaned_title": "AAA",
                    "new_custom_order": "!!!",
                    "previous_custom_order": self.CONFUSABLE_CUSTOM_ORDER,
                }
            ],
        }

    @pytest.mark.django_db
    def test_recalulate_preview_unknown_updated_confusables(self, site, alphabet):
        factories.CharacterFactory.create(site=site, title="A")
        factories.DictionaryEntryFactory.create(site=site, title="ᐱᐱᐱ")
        factories.DictionaryEntryFactory.create(site=site, title="abcd")
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")
        alphabet.input_to_canonical_map = [{"in": "ᐱ", "out": "A"}]
        alphabet.save()

        result = recalculate_custom_order_preview("test")
        assert result == {
            "unknown_character_count": {"⚑d": 1},
            "updated_entries": [
                {
                    "title": "abcd",
                    "cleaned_title": "abcd",
                    "new_custom_order": "#$%⚑d",
                    "previous_custom_order": "⚑a⚑b⚑c⚑d",
                },
                {
                    "title": "ᐱᐱᐱ",
                    "cleaned_title": "AAA",
                    "new_custom_order": "!!!",
                    "previous_custom_order": self.CONFUSABLE_CUSTOM_ORDER,
                },
            ],
        }

    @pytest.mark.django_db
    def test_recalulate_empty(self, site, alphabet):
        result = recalculate_custom_order(site.slug)

        assert result == []

    @pytest.mark.django_db
    def test_recalulate_updated_order(self, site, alphabet):
        factories.DictionaryEntryFactory.create(site=site, title="abc")
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")

        result = recalculate_custom_order("test")
        assert result == [
            {
                "title": "abc",
                "cleaned_title": "abc",
                "new_custom_order": "!#$",
                "previous_custom_order": "⚑a⚑b⚑c",
            }
        ]

    @pytest.mark.django_db
    def test_recalulate_updated_confusables(self, site, alphabet):
        factories.CharacterFactory.create(site=site, title="A")
        factories.DictionaryEntryFactory.create(site=site, title="ᐱᐱᐱ")
        alphabet.input_to_canonical_map = [{"in": "ᐱ", "out": "A"}]
        alphabet.save()

        result = recalculate_custom_order("test")
        assert result == [
            {
                "title": "ᐱᐱᐱ",
                "cleaned_title": "AAA",
                "new_custom_order": "!!!",
                "previous_custom_order": self.CONFUSABLE_CUSTOM_ORDER,
            }
        ]

    @pytest.mark.django_db
    def test_recalulate_updated_all(self, site, alphabet):
        factories.CharacterFactory.create(site=site, title="A")
        factories.DictionaryEntryFactory.create(site=site, title="ᐱbcd")
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")
        alphabet.input_to_canonical_map = [{"in": "ᐱ", "out": "A"}]
        alphabet.save()

        result = recalculate_custom_order("test")
        assert result == [
            {
                "title": "ᐱbcd",
                "cleaned_title": "Abcd",
                "new_custom_order": "!$%⚑d",
                "previous_custom_order": "⚑ᐱ⚑b⚑c⚑d",
            }
        ]
