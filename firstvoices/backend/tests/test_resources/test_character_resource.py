import uuid

import pytest
import tablib

from backend.models.characters import (
    Alphabet,
    Character,
    CharacterVariant,
    IgnoredCharacter,
)
from backend.resources.characters import (
    AlphabetConfusablesResource,
    CharacterResource,
    CharacterVariantResource,
    IgnoredCharacterResource,
)
from backend.tests.factories import (
    AlphabetFactory,
    AudioFactory,
    CharacterFactory,
    SiteFactory,
    VideoFactory,
)


@pytest.mark.skip("Tests are for initial migration only")
class TestCharacterImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "id,created,created_by,last_modified,last_modified_by,site,title,sort_order,approximate_form,"
            "related_audio,related_videos",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @staticmethod
    def base_import_validation(result, site, data):
        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Character.objects.filter(site=site.id).count() == len(data)

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Character object with basic fields"""
        site = SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,{site.id},ᐁ,1,e,{uuid.uuid4()},{uuid.uuid4()}",  # noqa E501
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,{site.id},ᐃ,2,,{uuid.uuid4()},{uuid.uuid4()}",  # noqa E501
        ]
        table = self.build_table(data)

        result = CharacterResource().import_data(dataset=table)

        self.base_import_validation(result, site, data)

        new_char = Character.objects.get(id=table["id"][0])
        assert table["title"][0] == new_char.title
        assert table["site"][0] == str(new_char.site.id)
        assert table["sort_order"][0] == str(new_char.sort_order)
        assert table["approximate_form"][0] == new_char.approximate_form

        new_char = Character.objects.get(id=table["id"][1])
        assert table["approximate_form"][1] == new_char.approximate_form

    @pytest.mark.django_db
    def test_related_media(self):
        site = SiteFactory.create()
        audio = AudioFactory.create()
        video = VideoFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,{site.id},ᐃ,2,t,{audio.id},{video.id}",  # noqa E501
        ]
        table = self.build_table(data)

        result = CharacterResource().import_data(dataset=table)

        self.base_import_validation(result, site, data)

        new_char = Character.objects.get(id=table["id"][0])
        # Verify audio and video are present
        assert new_char.related_audio.all().count() == 1
        assert new_char.related_audio.all().first().id == audio.id

        assert new_char.related_videos.all().count() == 1
        assert new_char.related_videos.all().first().id == video.id

    @pytest.mark.django_db
    def test_missing_related_media(self):
        site = SiteFactory.create()
        audio = AudioFactory.create(site=site)
        data = [
            f'{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,{site.id},ᐃ,2,,"{audio.id},{uuid.uuid4()}",{uuid.uuid4()}',  # noqa E501
        ]
        table = self.build_table(data)

        result = CharacterResource().import_data(dataset=table)

        self.base_import_validation(result, site, data)

        new_char = Character.objects.get(id=table["id"][0])
        # Verifying missing audio and video are not present
        assert new_char.related_audio.all().count() == 1
        assert audio in new_char.related_audio.all()
        assert new_char.related_videos.all().count() == 0

    @pytest.mark.django_db
    def test_empty_related_media(self):
        site = SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,{site.id},ᐃ,2,,,",  # noqa E501
        ]
        table = self.build_table(data)

        result = CharacterResource().import_data(dataset=table)

        self.base_import_validation(result, site, data)

        new_char = Character.objects.get(id=table["id"][0])
        # Verifying audio and video are not present
        assert new_char.related_audio.all().count() == 0
        assert new_char.related_videos.all().count() == 0

    @pytest.mark.django_db
    def test_multiple_related_media(self):
        site = SiteFactory.create()
        audio = AudioFactory.create()
        audio2 = AudioFactory.create()
        data = [
            f'{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,{site.id},ᐃ,2,,"{audio.id},{audio2.id}",',  # noqa E501
        ]
        table = self.build_table(data)

        result = CharacterResource().import_data(dataset=table)

        self.base_import_validation(result, site, data)

        new_char = Character.objects.get(id=table["id"][0])
        # Verify that character has 2 audio files and no video files
        assert new_char.related_audio.all().count() == 2
        assert new_char.related_videos.all().count() == 0


@pytest.mark.skip("Tests are for initial migration only")
class TestCharacterVariantImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "id,created,created_by,last_modified,last_modified_by,site,title,base_character_title,base_character",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Character object with basic fields"""
        site = SiteFactory.create()
        char_a = CharacterFactory.create(site=site, title="a")
        char_b = CharacterFactory.create(site=site, title="b")
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,{site.id},A,a,{char_a.id}",  # noqa E501
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,{site.id},B,b,{char_b.id}",  # noqa E501
        ]
        table = self.build_table(data)

        result = CharacterVariantResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert CharacterVariant.objects.filter(site=site.id).count() == len(data)

        new_variant = CharacterVariant.objects.get(id=table["id"][0])
        assert table["title"][0] == new_variant.title
        assert table["site"][0] == str(new_variant.site.id)
        assert table["base_character"][0] == str(new_variant.base_character.id)


@pytest.mark.skip("Tests are for initial migration only")
class TestIgnoredCharacterImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "id,created,created_by,last_modified,last_modified_by,site,title",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Character object with basic fields"""
        site = SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,{site.id},-",  # noqa E501
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-21 10:20:15.754,user_two@test.com,{site.id},.",  # noqa E501
        ]
        table = self.build_table(data)

        result = IgnoredCharacterResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert IgnoredCharacter.objects.filter(site=site.id).count() == len(data)

        new_char = IgnoredCharacter.objects.get(id=table["id"][0])
        assert table["title"][0] == new_char.title
        assert table["site"][0] == str(new_char.site.id)


@pytest.mark.skip("Tests are for initial migration only")
class TestAlphabetConfusablesImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            # these headers should match what is produced by fv-nuxeo-export tool
            "out_form,in_form,site",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    @pytest.mark.parametrize("alphabet_exists", (True, False))
    def test_import_confusable_mapper(self, alphabet_exists):
        """Import confusables JSON into Alphabet object"""
        site = SiteFactory.create()
        if alphabet_exists:
            AlphabetFactory.create(site=site)

        # this mapper should result in lowercasing
        data = [
            f"a,A,{site.id}",
            f"b,B,{site.id}",
        ]

        table = self.build_table(data)
        result = AlphabetConfusablesResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["skip"] == len(data)
        assert Alphabet.objects.filter(site=site.id).exists()

        alphabet = Alphabet.objects.get(site=site)
        assert len(alphabet.input_to_canonical_map) == len(data)

        mapper = {"in": "A", "out": "a"}
        assert mapper in alphabet.input_to_canonical_map
        assert alphabet.clean_confusables("ABC") == "abC"

    @pytest.mark.django_db
    def test_import_confusables_with_unicode(self):
        """Import confusables JSON into Alphabet object with correct unicode"""
        site = SiteFactory.create()

        data = [
            f"ƛ̓,λ̸̒,{site.id}",
        ]

        table = self.build_table(data)
        result = AlphabetConfusablesResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()

        alphabet = Alphabet.objects.get(site=site)
        mapper = {"in": "λ̸̒", "out": "ƛ̓"}
        assert mapper in alphabet.input_to_canonical_map
        assert alphabet.clean_confusables("λ̸̒a") == "ƛ̓a"
