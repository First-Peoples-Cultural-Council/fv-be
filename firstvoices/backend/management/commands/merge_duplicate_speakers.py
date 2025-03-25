import logging

from django.core.management.base import BaseCommand

from backend.models.media import Person


class Command(BaseCommand):
    help = "Merge duplicate speakers for all sites."

    def handle(self, *args, **options):
        # Setting logger level to get all logs
        logger = logging.getLogger(__name__)

        placeholder_bio = "---"
        people = list(Person.objects.all().order_by("-created"))
        logger.debug(f"Merging duplicates in {len(people)} people")

        for p in people:
            oldest_match = (
                Person.objects.filter(site=p.site, name__iexact=p.name)
                .exclude(pk=p.pk)
                .order_by("created")
                .first()
            )

            if oldest_match:
                self.merge_audio_links(oldest_match, p)

                if oldest_match.bio == "":
                    self.set_bio(oldest_match, placeholder_bio)

                p.delete()

        self.remove_placeholder_bios(placeholder_bio)

        people = Person.objects.all()
        logger.debug(f"Resulting non-duplicate people: {people.count()}")

    def remove_placeholder_bios(self, placeholder_bio):
        placeholders = list(Person.objects.filter(bio=placeholder_bio))
        for p in placeholders:
            p.bio = ""
            p.save()

    def set_bio(self, person, placeholder):
        # find oldest bio
        oldest_bio = (
            Person.objects.filter(site=person.site, name__iexact=person.name)
            .exclude(bio="")
            .exclude(pk=person.pk)
            .order_by("created")
            .first()
        )
        if oldest_bio:
            person.bio = oldest_bio.bio
        else:
            person.bio = placeholder
        person.save()

    def merge_audio_links(self, target, source):
        audios = source.audio_set.all()
        for a in audios:
            target.audio_set.add(a.pk)
