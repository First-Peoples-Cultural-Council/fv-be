import uuid

import pytest
import tablib

from backend.models import DictionaryEntry
from backend.models.constants import Visibility
from backend.models.dictionary import (
    DictionaryEntryCategory,
    DictionaryEntryLink,
    DictionaryEntryRelatedCharacter,
    TypeOfDictionaryEntry,
)
from backend.resources.dictionary import (
    DictionaryEntryCategoryResource,
    DictionaryEntryLinkResource,
    DictionaryEntryRelatedCharacterResource,
    DictionaryEntryResource,
)
from backend.tests import factories


# @pytest.mark.skip("Tests are for initial migration only")
class TestDictionaryEntryImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match the defined template for batch uploads
            "id,created,created_by,last_modified,last_modified_by,site,"
            "title,visibility,type,batch_id,include_on_kids_site,include_in_games,part_of_speech,"
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
            f"{site.id},test_word,Public,Word,batch_id,True,True,Noun,https://www.youtube.com/watch?v=A1bcde23f5g",
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_two@test.com,2023-02-02 21:21:39.864,user_two@test.com,"
            f"{site.id},test_phrase,Team,Phrase,batch_id,False,False,Verb,",
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
        assert table["batch_id"][0] == test_word.batch_id
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
        assert table["batch_id"][1] == test_phrase.batch_id
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
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
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


@pytest.mark.skip("Tests are for initial migration only")
class TestDictionaryEntryCategoryImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "id,created,created_by,last_modified,last_modified_by,site,dictionary_entry,category",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import DictionaryEntryCategory object with basic fields"""
        site = factories.SiteFactory.create()
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site)
        category = factories.CategoryFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{category.id}",
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{category.id}",
        ]

        table = self.build_table(data)
        result = DictionaryEntryCategoryResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert DictionaryEntryCategory.objects.filter(
            category=category.id
        ).count() == len(data)

        entry_category = DictionaryEntryCategory.objects.get(id=table["id"][0])
        assert table["site"][0] == str(entry_category.site.id)
        assert table["dictionary_entry"][0] == str(entry_category.dictionary_entry.id)
        assert table["category"][0] == str(entry_category.category.id)

    @pytest.mark.django_db
    def test_import_base_data_with_nonexistent_category(self):
        """Import DictionaryEntryCategory object with missing category"""
        site = factories.SiteFactory.create()
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site)
        category = factories.CategoryFactory.create(site=site)
        category2 = factories.CategoryFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{category.id}",
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{uuid.uuid4()}",  # non-existent category
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{category2.id}",
        ]

        table = self.build_table(data)
        result = DictionaryEntryCategoryResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 2
        assert result.totals["skip"] == 1
        assert result.totals["error"] == 0
        assert (
            DictionaryEntryCategory.objects.filter(
                dictionary_entry=dictionary_entry.id
            ).count()
            == 2
        )


@pytest.mark.skip("Tests are for initial migration only")
class TestDictionaryEntryRelatedCharacter:
    @staticmethod
    def build_table(data):
        headers = ["character,dictionary_entry,site,id"]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        site = factories.SiteFactory.create()
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site)
        character = factories.CharacterFactory.create(site=site)
        data = [
            f"{character.id},{dictionary_entry.id},{site.id},{uuid.uuid4()}",
        ]
        table = self.build_table(data)
        result = DictionaryEntryRelatedCharacterResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert DictionaryEntryRelatedCharacter.objects.filter(
            character=character.id
        ).count() == len(data)

        entry_related_character = DictionaryEntryRelatedCharacter.objects.get(
            id=table["id"][0]
        )
        assert table["character"][0] == str(entry_related_character.character.id)
        assert table["dictionary_entry"][0] == str(
            entry_related_character.dictionary_entry.id
        )


@pytest.mark.skip("Tests are for initial migration only")
class TestDictionaryLinkImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "id,created,created_by,last_modified,last_modified_by,site,dictionary_entry,related_entry",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import DictionaryEntryLink object with basic fields"""
        site = factories.SiteFactory.create()
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site)
        dictionary_entry2 = factories.DictionaryEntryFactory.create(site=site)
        dictionary_entry3 = factories.DictionaryEntryFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{dictionary_entry2.id}",
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{dictionary_entry3.id}",
        ]

        table = self.build_table(data)
        result = DictionaryEntryLinkResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert DictionaryEntryLink.objects.filter(
            from_dictionary_entry=dictionary_entry.id
        ).count() == len(data)

        entry_link = DictionaryEntryLink.objects.get(id=table["id"][0])
        assert table["site"][0] == str(entry_link.site.id)
        assert table["dictionary_entry"][0] == str(entry_link.from_dictionary_entry.id)
        assert table["related_entry"][0] == str(entry_link.to_dictionary_entry.id)

    @pytest.mark.django_db
    def test_import_base_data_with_nonexistent_dictionary_entry(self):
        """Import DictionaryEntryLink object with missing dictionary entry"""
        site = factories.SiteFactory.create()
        dictionary_entry = factories.DictionaryEntryFactory.create(site=site)
        dictionary_entry2 = factories.DictionaryEntryFactory.create(site=site)
        dictionary_entry3 = factories.DictionaryEntryFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{dictionary_entry2.id}",
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{uuid.uuid4()}",  # containing non-existent entry
            f"{uuid.uuid4()},,,,,{site.id},{dictionary_entry.id},{dictionary_entry3.id}",
        ]

        table = self.build_table(data)
        result = DictionaryEntryLinkResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 2
        assert result.totals["skip"] == 1
        assert result.totals["error"] == 0
        assert (
            DictionaryEntryLink.objects.filter(
                from_dictionary_entry=dictionary_entry.id
            ).count()
            == 2
        )
