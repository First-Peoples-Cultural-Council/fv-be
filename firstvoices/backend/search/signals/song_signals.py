from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.models import Lyric, Song
from backend.search import ES_RETRY_POLICY
from backend.search.tasks.song_tasks import (
    delete_from_index,
    update_lyrics,
    update_song_index,
)
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=Song)
def request_update_song_index(sender, instance, **kwargs):
    if Song.objects.filter(id=instance.id).exists():
        update_song_index.apply_async(
            (instance.id,),
            link_error=link_error_handler.s(),
            retry=True,
            retry_policy=ES_RETRY_POLICY,
        )


# Delete entry from index
@receiver(post_delete, sender=Song)
def request_delete_from_index(sender, instance, **kwargs):
    delete_from_index.apply_async((instance.id,), link_error=link_error_handler.s())


# Lyrics update
@receiver(post_delete, sender=Lyric)
@receiver(post_save, sender=Lyric)
def request_update_lyrics_index(sender, instance, **kwargs):
    update_lyrics.apply_async(
        (
            instance.id,
            instance.song.id,
        ),
        link_error=link_error_handler.s(),
        retry=True,
        retry_policy=ES_RETRY_POLICY,
    )