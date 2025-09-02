import uuid

import pytest
import tablib

from backend.models import DictionaryEntry
from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.resources.dictionary import DictionaryEntryResource
from backend.tests import factories


@pytest.mark.skip("Tests are for initial migration only")
class TestDictionaryEntryImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match the defined template for batch uploads
            "id,created,created_by,last_modified,last_modified_by,site,"
            "title,visibility,type,legacy_batch_filename,include_on_kids_site,include_in_games,part_of_speech,"
            "related_video_links"
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import DictionaryEntry object with basic fields"""
        site = factories.SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f"{site.id},test_word,Public,Word,legacy_batch_filename,True,True,Noun,"
            f"https://www.youtube.com/watch?v=A1bcde23f5g",
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_two@test.com,2023-02-02 21:21:39.864,user_two@test.com,"
            f"{site.id},test_phrase,Team,Phrase,legacy_batch_filename,False,False,Verb,",
        ]

        table = self.build_table(data)
        result = DictionaryEntryResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert DictionaryEntry.objects.filter(site=site.id).count() == len(data)

        test_word = DictionaryEntry.objects.get(id=table["id"][0])
        assert table["title"][0] == test_word.title
        assert table["site"][0] == str(test_word.site.id)
        assert Visibility.PUBLIC == test_word.visibility
        assert TypeOfDictionaryEntry.WORD == test_word.type
        assert table["legacy_batch_filename"][0] == test_word.legacy_batch_filename
        assert not test_word.exclude_from_kids
        assert not test_word.exclude_from_games
        assert table["part_of_speech"][0] == test_word.part_of_speech.title
        assert test_word.related_video_links == table["related_video_links"][0].split(
            ","
        )

        test_phrase = DictionaryEntry.objects.get(id=table["id"][1])
        assert table["title"][1] == test_phrase.title
        assert table["site"][1] == str(test_phrase.site.id)
        assert Visibility.TEAM == test_phrase.visibility
        assert TypeOfDictionaryEntry.PHRASE == test_phrase.type
        assert table["legacy_batch_filename"][1] == test_phrase.legacy_batch_filename
        assert test_phrase.exclude_from_kids
        assert test_phrase.exclude_from_games
        assert table["part_of_speech"][1] == test_phrase.part_of_speech.title


class BaseDictionaryEntryContentTest:
    content_type = ""
    model = None
    resource = None

    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match the defined template for batch uploads
            "id,created,created_by,last_modified,last_modified_by,site,dictionary_entry,text",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import DictionaryEntry content object with standard fields"""
        site = factories.SiteFactory.create()
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f"{site.id},{dictionary_entry.id},this is a {self.content_type}",
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com, "
            f"{site.id},{dictionary_entry.id},this is a {self.content_type}",
        ]

        table = self.build_table(data)
        result = self.resource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert self.model.objects.filter(
            dictionary_entry=dictionary_entry.id
        ).count() == len(data)

        content = self.model.objects.get(id=table["id"][0])
        assert table["text"][0] == content.text
        assert table["site"][0] == str(content.site.id)
        assert table["dictionary_entry"][0] == str(content.dictionary_entry.id)
