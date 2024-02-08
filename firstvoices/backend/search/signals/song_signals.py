from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.models import Lyric, Song
from backend.search.tasks import song_index_tasks
from firstvoices.celery import link_error_handler


@receiver(post_save, sender=Song)
def sync_song_in_index(sender, instance, **kwargs):
    song_index_tasks.sync_song_in_index.apply_async(
        (instance.id,), link_error=link_error_handler.s()
    )


@receiver(post_delete, sender=Song)
def remove_song_from_index(sender, instance, **kwargs):
    song_index_tasks.remove_song_from_index.apply_async(
        (instance.id,), link_error=link_error_handler.s()
    )


@receiver(post_delete, sender=Lyric)
@receiver(post_save, sender=Lyric)
def sync_song_lyrics_in_index(sender, instance, **kwargs):
    song_index_tasks.sync_song_in_index.apply_async(
        (instance.song.id,), link_error=link_error_handler.s()
    )
