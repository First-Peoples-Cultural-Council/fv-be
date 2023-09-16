import uuid

import pytest
import tablib

from backend.models.media import (
    Audio,
    AudioSpeaker,
    File,
    Image,
    ImageFile,
    Person,
    Video,
    VideoFile,
)
from backend.resources.media import (
    AudioResource,
    AudioSpeakerMigrationResource,
    AudioSpeakerResource,
    ImageResource,
    PersonResource,
    VideoResource,
)
from backend.tests.factories import AudioFactory, PersonFactory, SiteFactory


class TestPersonImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,name,bio,site",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Person object with basic fields"""
        site = SiteFactory.create()
        data = [
            f"{uuid.uuid4()},2019-05-08 12:11:02.372,user_one@test.com,2019-12-19 09:23:07.303,user_two@test.com,Clifford,Yes it's Clifford the Big Red Dog.,{site.id}",  # noqa E501
            f"{uuid.uuid4()},2020-05-23 03:48:21.202,user_one@test.com,2023-01-24 15:27:43.969,user_two@test.com,My Favorite Person,,{site.id}",  # noqa E501
        ]
        table = self.build_table(data)

        result = PersonResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Person.objects.filter(site=site.id).count() == len(data)

        new_person = Person.objects.get(id=table["id"][0])
        assert table["name"][0] == new_person.name
        assert table["site"][0] == str(new_person.site.id)
        assert table["bio"][0] == new_person.bio


class BaseMediaImportTest:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,title,description,acknowledgement,is_shared,"
            "fvm_for_kids,fvaudience_for_kids,nuxeo_file_name,site,exclude_from_kids,content",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table


class TestAudioImport(BaseMediaImportTest):
    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Audio model with basic fields"""
        site = SiteFactory.create()
        id_one = uuid.uuid4()
        id_two = uuid.uuid4()
        data = [
            f"{id_one},2019-12-09 10:15:11.896,user_one@test.com,2019-12-19 09:23:50.656,user_two@test.com,Woof Woof,"
            f"Sound of a dog barking,Recorded by: My Mom,True,False,,somefile.mp3,{site.id},False,{site.slug}/"
            f"{id_one}/somefile.mp3",
            f"{id_two},2019-12-13 08:57:33.654,user_one@test.com,2020-07-14 13:54:26.485,user_two@test.com,Meow,"
            f"Great sound from my cat Fluffy,,False,False,,my_cool_meow_file.mp3.mp3,{site.id},True,{site.slug}/"
            f"{id_two}/my_cool_meow_file.mp3.mp3",
        ]
        table = self.build_table(data)

        result = AudioResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Audio.objects.filter(site=site.id).count() == len(data)
        assert File.objects.filter(site=site.id).count() == len(data)

        new_audio = Audio.objects.get(id=table["id"][0])
        assert table["title"][0] == new_audio.title
        assert table["site"][0] == str(new_audio.site.id)
        assert table["description"][0] == new_audio.description
        assert table["acknowledgement"][0] == new_audio.acknowledgement
        assert table["is_shared"][0] == str(new_audio.is_shared)
        assert table["exclude_from_kids"][0] == str(new_audio.exclude_from_kids)
        assert table["content"][0] == str(new_audio.original.content)

    @pytest.mark.django_db
    def test_import_empty_metadata(self):
        """Import Audio model with metadata missing"""
        site = SiteFactory.create()
        id_one = uuid.uuid4()
        data = [
            f"{id_one},,,,,Woof Woof,"
            f"Sound of a dog barking,Recorded by: My Mom,True,False,,somefile.mp3,{site.id},False,{site.slug}/"
            f"{id_one}/somefile.mp3",
        ]
        table = self.build_table(data)
        result = AudioResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Audio.objects.filter(site=site.id).count() == 1
        assert File.objects.filter(site=site.id).count() == 1
        assert (
            Audio.objects.get(id=table["id"][0]).original
            == File.objects.filter(site=site.id).first()
        )


class TestAudioSpeakerImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,speaker,site,audio",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_relation(self):
        """Import working Audio-Person link in AudioSpeaker table"""
        site = SiteFactory.create()
        audio = AudioFactory.create(site=site)
        speaker = PersonFactory.create(site=site)
        data = [
            f"{uuid.uuid4()},2019-12-09 10:15:11.896,user_one@test.com,2019-12-19 09:23:50.656,user_two@test.com,{speaker.id},{site.id},{audio.id}",  # noqa E501
        ]
        table = self.build_table(data)

        result = AudioSpeakerResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)

        assert AudioSpeaker.objects.filter(audio=audio.id).count() == 1
        assert AudioSpeaker.objects.filter(speaker=speaker.id).count() == 1

        speaker_link = AudioSpeaker.objects.get(id=table["id"][0])
        assert speaker_link.audio == audio
        assert speaker_link.speaker == speaker

    @pytest.mark.django_db
    def test_delete_non_speaker_persons(self):
        """After migrating AudioSpeakers, delete unused Persons on the site"""
        site = SiteFactory.create()
        audio = AudioFactory.create(site=site)
        speaker = PersonFactory.create(site=site)
        PersonFactory.create(site=site)  # unused person

        unrelated_site = SiteFactory.create()
        PersonFactory.create(site=unrelated_site)  # person on other site

        data = [
            f"{uuid.uuid4()},2019-12-09 10:15:11.896,user_one@test.com,2019-12-19 09:23:50.656,user_two@test.com,{speaker.id},{site.id},{audio.id}",  # noqa E501
        ]
        table = self.build_table(data)

        result = AudioSpeakerMigrationResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)

        # 2 speakers created on this site, only the one in use remains
        assert Person.objects.filter(site=site).count() == 1
        assert Person.objects.filter(id=speaker.id).count() == 1
        # other site is unaffected
        assert Person.objects.filter(site=unrelated_site).count() == 1


class TestImageImport(BaseMediaImportTest):
    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Image model with basic fields"""
        site = SiteFactory.create()
        id_one = uuid.uuid4()
        id_two = uuid.uuid4()
        data = [
            f"{id_one},2019-12-09 10:15:11.896,user_one@test.com,2019-12-19 09:23:50.656,user_two@test.com,Woof Woof,"
            f"Image of a dog barking,Recorded by: My Mom,True,False,,somefile.jpg,{site.id},False,{site.slug}/"
            f"{id_one}/somefile.jpg",
            f"{id_two},2019-12-13 08:57:33.654,user_one@test.com,2020-07-14 13:54:26.485,user_two@test.com,Meow,"
            f"Great image from my cat Fluffy,,False,False,,my_cool_meow_file.jpg.jpg,{site.id},True,{site.slug}/"
            f"{id_two}/my_cool_meow_file.jpg.jpg",
        ]
        table = self.build_table(data)

        result = ImageResource().import_data(dataset=table)
        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Image.objects.filter(site=site.id).count() == len(data)
        assert ImageFile.objects.filter(site=site.id).count() == len(data)

        new_image = Image.objects.get(id=table["id"][0])
        assert table["title"][0] == new_image.title
        assert table["site"][0] == str(new_image.site.id)
        assert table["description"][0] == new_image.description
        assert table["acknowledgement"][0] == new_image.acknowledgement
        assert table["is_shared"][0] == str(new_image.is_shared)
        assert table["exclude_from_kids"][0] == str(new_image.exclude_from_kids)
        assert table["content"][0] == str(new_image.original.content)


class TestVideoImport(BaseMediaImportTest):
    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Video model with basic fields"""
        site = SiteFactory.create()
        id_one = uuid.uuid4()
        id_two = uuid.uuid4()
        data = [
            f"{id_one},2019-12-09 10:15:11.896,user_one@test.com,2019-12-19 09:23:50.656,user_two@test.com,Woof Woof,"
            f"Video of a dog barking,Recorded by: My Mom,True,False,,somefile.mp4,{site.id},False,{site.slug}/"
            f"{id_one}/somefile.mp4",
            f"{id_two},2019-12-13 08:57:33.654,user_one@test.com,2020-07-14 13:54:26.485,user_two@test.com,Meow,"
            f"Great video from my cat Fluffy,,False,False,,my_cool_meow_file.mp4.mp4,{site.id},True,{site.slug}/"
            f"{id_two}/my_cool_meow_file.mp4.mp4",
        ]
        table = self.build_table(data)

        result = VideoResource().import_data(dataset=table)
        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Video.objects.filter(site=site.id).count() == len(data)
        assert VideoFile.objects.filter(site=site.id).count() == len(data)

        new_video = Video.objects.get(id=table["id"][0])
        assert table["title"][0] == new_video.title
        assert table["site"][0] == str(new_video.site.id)
        assert table["description"][0] == new_video.description
        assert table["acknowledgement"][0] == new_video.acknowledgement
        assert table["is_shared"][0] == str(new_video.is_shared)
        assert table["exclude_from_kids"][0] == str(new_video.exclude_from_kids)
        assert table["content"][0] == str(new_video.original.content)
