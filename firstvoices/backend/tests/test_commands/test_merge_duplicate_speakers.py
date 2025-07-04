import pytest
from django.core.management import call_command

from backend.models.media import Person
from backend.tests import factories


@pytest.mark.django_db
class TestMergeDuplicateSpeakers:
    def test_merge_preserves_oldest_instances(self):
        site = factories.SiteFactory.create()
        person_a1 = factories.PersonFactory.create(name="person A", site=site)
        person_a2 = factories.PersonFactory.create(name="person A", site=site)
        person_b1 = factories.PersonFactory.create(name="person b", site=site)
        person_b2 = factories.PersonFactory.create(name="person b", site=site)

        call_command("merge_duplicate_speakers")
        merged_persons = Person.objects.all()
        assert merged_persons.count() == 2

        assert Person.objects.filter(pk=person_a1.pk).count() == 1
        assert Person.objects.filter(pk=person_b1.pk).count() == 1

        assert Person.objects.filter(pk=person_a2.pk).count() == 0
        assert Person.objects.filter(pk=person_b2.pk).count() == 0

    def test_merge_case_insensitive(self):
        site = factories.SiteFactory.create()
        factories.PersonFactory.create(name="person A", site=site)
        factories.PersonFactory.create(name="PERSON A", site=site)
        factories.PersonFactory.create(name="Person a", site=site)

        call_command("merge_duplicate_speakers")
        assert Person.objects.all().count() == 1

    def test_no_merging_different_sites(self):
        factories.PersonFactory.create(name="PERSON A")
        factories.PersonFactory.create(name="PERSON A")
        factories.PersonFactory.create(name="PERSON A")

        call_command("merge_duplicate_speakers")
        assert Person.objects.all().count() == 3

    def test_no_merging_different_names(self):
        site = factories.SiteFactory.create()
        factories.PersonFactory.create(name="person A", site=site)
        factories.PersonFactory.create(name="PERSON b", site=site)
        factories.PersonFactory.create(name="Person C", site=site)

        call_command("merge_duplicate_speakers")
        assert Person.objects.all().count() == 3

    def test_merge_preserves_audio_links(self):
        site = factories.SiteFactory.create()
        person_a1 = factories.PersonFactory.create(name="person A", site=site)
        person_a2 = factories.PersonFactory.create(name="PERSON A", site=site)
        person_a3 = factories.PersonFactory.create(name="Person a", site=site)

        audio_1 = factories.AudioFactory.create(site=site)
        audio_1.speakers.add(person_a1)

        audio_2 = factories.AudioFactory.create(site=site)
        audio_2.speakers.add(person_a2)

        audio_3 = factories.AudioFactory.create(site=site)
        audio_3.speakers.add(person_a3)

        call_command("merge_duplicate_speakers")
        merged_audio = Person.objects.first().audio_set.values_list("id", flat=True)
        assert audio_1.pk in merged_audio
        assert audio_2.pk in merged_audio
        assert audio_3.pk in merged_audio

    def test_no_duplicate_audio_links(self):
        site = factories.SiteFactory.create()
        person_a1 = factories.PersonFactory.create(name="person A", site=site)
        person_a2 = factories.PersonFactory.create(name="PERSON A", site=site)
        person_a3 = factories.PersonFactory.create(name="Person a", site=site)

        audio_1 = factories.AudioFactory.create(site=site)
        audio_1.speakers.add(person_a1)
        audio_1.speakers.add(person_a2)
        audio_1.speakers.add(person_a3)

        call_command("merge_duplicate_speakers")
        merged_audio = Person.objects.first().audio_set.all()
        assert merged_audio.count() == 1

    def test_keep_oldest_bio(self):
        site = factories.SiteFactory.create()
        factories.PersonFactory.create(name="person A", site=site)
        factories.PersonFactory.create(name="PERSON A", site=site, bio="A great life.")
        factories.PersonFactory.create(
            name="Person a", site=site, bio="New updates on a great life."
        )
        factories.PersonFactory.create(name="Person a", site=site)

        call_command("merge_duplicate_speakers")
        merged_person = Person.objects.first()
        assert merged_person.bio == "A great life."

    def test_all_bios_blank(self):
        site = factories.SiteFactory.create()
        factories.PersonFactory.create(name="person A", site=site)
        factories.PersonFactory.create(name="PERSON A", site=site)
        factories.PersonFactory.create(name="Person a", site=site)

        call_command("merge_duplicate_speakers")
        merged_person = Person.objects.first()
        assert merged_person.bio == ""

    def test_system_last_modified_speaker(self):
        site = factories.SiteFactory.create()
        person_1 = factories.PersonFactory.create(name="person A", site=site)
        factories.PersonFactory.create(name="PERSON A", site=site, bio="A great life.")

        call_command("merge_duplicate_speakers")
        updated_person = Person.objects.filter(id=person_1.id).first()
        assert updated_person.bio == "A great life."
        assert person_1.system_last_modified < updated_person.system_last_modified
