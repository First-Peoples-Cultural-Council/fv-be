import pytest

from backend.models import Alphabet, DictionaryEntry
from backend.tasks.alphabet_tasks import (
    recalculate_custom_order,
    recalculate_custom_order_preview,
)
from backend.tasks.utils import ASYNC_TASK_END_TEMPLATE
from backend.tests import factories


class TestAlphabetTasks:
    CONFUSABLE_PREV_CUSTOM_ORDER = "⚑ᐱ⚑ᐱ⚑ᐱ"

    @pytest.fixture
    def site(self):
        return factories.SiteFactory.create(slug="test")

    @pytest.fixture
    def alphabet(self, site):
        return factories.AlphabetFactory.create(site=site)

    @staticmethod
    def assert_async_task_logs(site, caplog):
        assert f"Task started. Additional info: site_slug: {site.slug}." in caplog.text
        assert ASYNC_TASK_END_TEMPLATE in caplog.text

    @pytest.mark.django_db
    def test_recalculate_preview_empty(self, site, alphabet, caplog):
        result = recalculate_custom_order_preview(site_slug=site.slug)

        assert result == {"unknown_character_count": {}, "updated_entries": []}

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_preview_unknown_only(self, site, alphabet, caplog):
        factories.DictionaryEntryFactory.create(site=site, title="abc")

        result = recalculate_custom_order_preview(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {"⚑a": 1, "⚑b": 1, "⚑c": 1},
            "updated_entries": [],
        }

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_preview_updated_custom_order_only(
        self, site, alphabet, caplog
    ):
        factories.DictionaryEntryFactory.create(site=site, title="abc")
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")

        result = recalculate_custom_order_preview(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [
                {
                    "title": "abc",
                    "is_title_updated": False,
                    "cleaned_title": "",
                    "new_custom_order": "!#$",
                    "previous_custom_order": "⚑a⚑b⚑c",
                }
            ],
        }

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_preview_updated_confusables_only(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="A")
        factories.DictionaryEntryFactory.create(site=site, title="ᐱᐱᐱ")
        alphabet.input_to_canonical_map = [{"in": "ᐱ", "out": "A"}]
        alphabet.save()

        result = recalculate_custom_order_preview(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [
                {
                    "title": "ᐱᐱᐱ",
                    "is_title_updated": True,
                    "cleaned_title": "AAA",
                    "new_custom_order": "!!!",
                    "previous_custom_order": self.CONFUSABLE_PREV_CUSTOM_ORDER,
                }
            ],
        }

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_preview_full_update(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="A")
        factories.DictionaryEntryFactory.create(site=site, title="ᐱᐱᐱ")
        factories.DictionaryEntryFactory.create(site=site, title="abcd")
        factories.DictionaryEntryFactory.create(site=site, title="ᐱbcd")
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")
        alphabet.input_to_canonical_map = [{"in": "ᐱ", "out": "A"}]
        alphabet.save()

        result = recalculate_custom_order_preview(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {"⚑d": 2},
            "updated_entries": [
                {
                    "title": "abcd",
                    "is_title_updated": False,
                    "cleaned_title": "",
                    "new_custom_order": "#$%⚑d",
                    "previous_custom_order": "⚑a⚑b⚑c⚑d",
                },
                {
                    "title": "ᐱbcd",
                    "is_title_updated": True,
                    "cleaned_title": "Abcd",
                    "new_custom_order": "!$%⚑d",
                    "previous_custom_order": "⚑ᐱ⚑b⚑c⚑d",
                },
                {
                    "title": "ᐱᐱᐱ",
                    "is_title_updated": True,
                    "cleaned_title": "AAA",
                    "new_custom_order": "!!!",
                    "previous_custom_order": self.CONFUSABLE_PREV_CUSTOM_ORDER,
                },
            ],
        }

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_preview_unaffected(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")
        factories.DictionaryEntryFactory.create(site=site, title="abc")
        factories.DictionaryEntryFactory.create(site=site, title="cab")

        result = recalculate_custom_order_preview(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [],
        }

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_preview_unknown_character_unaffected(
        self, site, alphabet, caplog
    ):
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")
        factories.DictionaryEntryFactory.create(site=site, title="abcx")

        result = recalculate_custom_order_preview(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {"⚑x": 1},
            "updated_entries": [],
        }

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_preview_multichar(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.DictionaryEntryFactory.create(site=site, title="aab")
        factories.CharacterFactory.create(site=site, title="aa")

        result = recalculate_custom_order_preview(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [
                {
                    "title": "aab",
                    "is_title_updated": False,
                    "cleaned_title": "",
                    "previous_custom_order": "!!#",
                    "new_custom_order": "$#",
                }
            ],
        }

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_empty(self, site, alphabet, caplog):
        result = recalculate_custom_order(site.slug)

        assert result == {
            "unknown_character_count": {},
            "updated_entries": [],
        }

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_unknown_only(self, site, alphabet, caplog):
        factories.DictionaryEntryFactory.create(site=site, title="abc")

        result = recalculate_custom_order(site.slug)
        assert result == {
            "unknown_character_count": {"⚑a": 1, "⚑b": 1, "⚑c": 1},
            "updated_entries": [],
        }

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_updated_custom_order_only(self, site, alphabet, caplog):
        entry = factories.DictionaryEntryFactory.create(site=site, title="abc")
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")

        result = recalculate_custom_order(site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [
                {
                    "title": "abc",
                    "cleaned_title": "",
                    "is_title_updated": False,
                    "new_custom_order": "!#$",
                    "previous_custom_order": "⚑a⚑b⚑c",
                }
            ],
        }
        assert DictionaryEntry.objects.get(id=entry.id).custom_order == "!#$"

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_updated_confusables_only(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="A")
        entry = factories.DictionaryEntryFactory.create(site=site, title="ᐱᐱᐱ")
        alphabet.input_to_canonical_map = [{"in": "ᐱ", "out": "A"}]
        alphabet.save()

        result = recalculate_custom_order(site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [
                {
                    "title": "ᐱᐱᐱ",
                    "cleaned_title": "AAA",
                    "is_title_updated": True,
                    "new_custom_order": "!!!",
                    "previous_custom_order": self.CONFUSABLE_PREV_CUSTOM_ORDER,
                }
            ],
        }
        updated_entry = DictionaryEntry.objects.get(id=entry.id)
        assert updated_entry.title == "AAA"
        assert updated_entry.custom_order == "!!!"

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_updated_full_update_single(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="A")
        entry = factories.DictionaryEntryFactory.create(site=site, title="ᐱbcd")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")
        alphabet.input_to_canonical_map = [{"in": "ᐱ", "out": "A"}]
        alphabet.save()

        result = recalculate_custom_order(site.slug)
        assert result == {
            "unknown_character_count": {"⚑d": 1},
            "updated_entries": [
                {
                    "title": "ᐱbcd",
                    "cleaned_title": "Abcd",
                    "is_title_updated": True,
                    "new_custom_order": "!#$⚑d",
                    "previous_custom_order": "⚑ᐱ⚑b⚑c⚑d",
                }
            ],
        }
        updated_entry = DictionaryEntry.objects.get(id=entry.id)
        assert updated_entry.title == "Abcd"
        assert updated_entry.custom_order == "!#$⚑d"

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_unaffected(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")
        entry1 = factories.DictionaryEntryFactory.create(site=site, title="abc")
        entry2 = factories.DictionaryEntryFactory.create(site=site, title="cab")

        result = recalculate_custom_order(site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [],
        }

        updated_entry1 = DictionaryEntry.objects.get(id=entry1.id)
        updated_entry2 = DictionaryEntry.objects.get(id=entry2.id)
        assert updated_entry1.title == "abc"
        assert updated_entry1.custom_order == "!#$"
        assert updated_entry2.title == "cab"
        assert updated_entry2.custom_order == "$!#"

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_unknown_character_unaffected(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        factories.CharacterFactory.create(site=site, title="c")
        entry = factories.DictionaryEntryFactory.create(site=site, title="abcx")

        result = recalculate_custom_order(site.slug)
        assert result == {
            "unknown_character_count": {"⚑x": 1},
            "updated_entries": [],
        }

        updated_entry = DictionaryEntry.objects.get(id=entry.id)
        assert updated_entry.title == "abcx"
        assert updated_entry.custom_order == "!#$⚑x"

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_multichar(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        entry = factories.DictionaryEntryFactory.create(site=site, title="aab")
        factories.CharacterFactory.create(site=site, title="aa")

        result = recalculate_custom_order(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [
                {
                    "title": "aab",
                    "cleaned_title": "",
                    "is_title_updated": False,
                    "previous_custom_order": "!!#",
                    "new_custom_order": "$#",
                }
            ],
        }

        updated_entry = DictionaryEntry.objects.get(id=entry.id)
        assert updated_entry.title == "aab"
        assert updated_entry.custom_order == "$#"

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_last_modified_not_updated(self, site, alphabet, caplog):
        factories.CharacterFactory.create(site=site, title="a")
        factories.CharacterFactory.create(site=site, title="b")
        entry = factories.DictionaryEntryFactory.create(site=site, title="abc")
        entry_last_modified = entry.last_modified
        factories.CharacterFactory.create(site=site, title="c")

        result = recalculate_custom_order(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [
                {
                    "title": "abc",
                    "cleaned_title": "",
                    "is_title_updated": False,
                    "previous_custom_order": "!#⚑c",
                    "new_custom_order": "!#$",
                }
            ],
        }
        entry = DictionaryEntry.objects.get(site=site, title="abc")
        assert entry.last_modified == entry_last_modified

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_preview_alphabet_missing(self, site, caplog):
        assert Alphabet.objects.count() == 0
        result = recalculate_custom_order_preview(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [],
        }
        assert Alphabet.objects.count() == 1

        self.assert_async_task_logs(site, caplog)

    @pytest.mark.django_db
    def test_recalculate_alphabet_missing(self, site, caplog):
        assert Alphabet.objects.count() == 0
        result = recalculate_custom_order(site_slug=site.slug)
        assert result == {
            "unknown_character_count": {},
            "updated_entries": [],
        }
        assert Alphabet.objects.count() == 1

        self.assert_async_task_logs(site, caplog)
