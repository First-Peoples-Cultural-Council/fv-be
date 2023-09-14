import uuid

import pytest
import tablib

from backend.models import Lyric, Song
from backend.resources.songs import LyricResource, SongResource
from backend.tests import factories


class TestSongsImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,visibility,title,introduction,exclude_from_games,"
            "site,title_translation,acknowledgements,notes,introduction_translation,exclude_from_kids,hide_overlay,"
            "related_audio,related_images,related_videos"
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        """Import Song object with basic fields"""
        site = factories.SiteFactory.create()
        audio_one = factories.AudioFactory.create(site=site)
        audio_two = factories.AudioFactory.create(site=site)
        image = factories.ImageFactory.create(site=site)
        video = factories.VideoFactory.create(site=site)

        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f"Public,Sample Song,Sample introduction,False,{site.id},Sample title translation,"
            f'"Sample acknowledgement one, with comma|Sample acknowledgement two","Sample note one|Sample note two",'
            f'Sample intro translation,False,False,"{audio_one.id},{audio_two.id}",{image.id},{video.id}'
        ]
        table = self.build_table(data)

        assert len(Song.objects.all()) == 0

        result = SongResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == len(data)
        assert Song.objects.filter(site=site.id).count() == len(data)

        new_song = Song.objects.get(id=table["id"][0])
        assert new_song.title == table["title"][0]
        assert new_song.title_translation == table["title_translation"][0]
        assert new_song.introduction == table["introduction"][0]
        assert new_song.introduction_translation == table["introduction_translation"][0]
        assert new_song.acknowledgements == table["acknowledgements"][0].split("|")
        assert new_song.notes == table["notes"][0].split("|")
        assert new_song.hide_overlay == eval(table["hide_overlay"][0])
        assert new_song.exclude_from_games == eval(table["exclude_from_games"][0])
        assert new_song.exclude_from_kids == eval(table["exclude_from_kids"][0])
        related_audio_string_list = [
            str(audio_id)
            for audio_id in new_song.related_audio.values_list("id", flat=True)
        ]
        assert table["related_audio"][0].split(",")[0] in related_audio_string_list
        assert table["related_audio"][0].split(",")[1] in related_audio_string_list
        assert str(new_song.related_images.first().id) == table["related_images"][0]
        assert str(new_song.related_videos.first().id) == table["related_videos"][0]
        assert new_song.get_visibility_display() == table["visibility"][0]
        assert str(new_song.site.id) == table["site"][0]


class TestLyricsImport:
    @staticmethod
    def build_table(data: list[str]):
        headers = [
            "id,created,created_by,last_modified,last_modified_by,parent_id,text,translation,ordering,notes",
        ]
        table = tablib.import_set("\n".join(headers + data), format="csv")
        return table

    @pytest.mark.django_db
    def test_import_base_data(self):
        site = factories.SiteFactory.create()
        song = factories.SongFactory.create(site=site)

        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f"{uuid.uuid4()},Test non lyric book entry one,Test lyric translation,0,",
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f"{song.id},Test lyric text,Test lyric translation,0,",
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f"{uuid.uuid4()},Test non lyric book entry two,Test translation,0,",
        ]
        table = self.build_table(data)

        assert len(Lyric.objects.all()) == 0
        assert song.lyrics.count() == 0

        result = LyricResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 1
        assert result.totals["skip"] == 2
        assert Lyric.objects.all().count() == 1

        new_lyric = Lyric.objects.get(id=table["id"][1])
        assert new_lyric.text == table["text"][1]
        assert new_lyric.translation == table["translation"][1]
        assert new_lyric.ordering == int(table["ordering"][1])
        assert new_lyric.song == song

    @pytest.mark.django_db
    def test_import_book_note_to_song_note(self):
        site = factories.SiteFactory.create()
        song = factories.SongFactory.create(site=site, notes=["Test note one"])

        data = [
            f"{uuid.uuid4()},2023-02-02 21:21:10.713,user_one@test.com,2023-02-02 21:21:39.864,user_one@test.com,"
            f"{song.id},Test lyric text,Test lyric translation,0,Lyric note one||| Lyric note two ",
        ]
        table = self.build_table(data)

        assert len(Lyric.objects.all()) == 0
        assert song.lyrics.count() == 0
        assert Song.objects.all().count() == 1

        result = LyricResource().import_data(dataset=table)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        assert result.totals["new"] == 1
        assert Lyric.objects.all().count() == 1

        assert Song.objects.all().count() == 1
        updated_song = Song.objects.get(id=song.id)
        assert updated_song.notes[0] == "Test note one"
        assert updated_song.notes[1] == "From lyric: Lyric note one"
        assert updated_song.notes[2] == "From lyric: Lyric note two"
