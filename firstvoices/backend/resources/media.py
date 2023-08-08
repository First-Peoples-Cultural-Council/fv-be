from backend.models.media import Audio, AudioSpeaker, Person
from backend.resources.base import SiteContentResource


class PersonResource(SiteContentResource):
    class Meta:
        model = Person


class AudioResource(SiteContentResource):
    class Meta:
        model = Audio


class AudioSpeakerResource(SiteContentResource):
    class Meta:
        model = AudioSpeaker


class AudioSpeakerMigrationResource(AudioSpeakerResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        """Delete unused persons that are not used as AudioSpeakers."""
        if not dry_run:
            Person.objects.filter(site__in=dataset["site"]).exclude(
                id__in=dataset["speaker"]
            ).delete()
