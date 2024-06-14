from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from backend.models import Lyric, Song
from backend.search.indexing.song_index import SongDocumentManager
from backend.search.tasks.index_manager_tasks import (
    request_remove_from_index,
    request_sync_in_index,
    request_update_in_index,
)


@receiver(post_save, sender=Song)
def sync_song_in_index(sender, instance, **kwargs):
    request_sync_in_index(SongDocumentManager, instance)


@receiver(post_delete, sender=Song)
def remove_song_from_index(sender, instance, **kwargs):
    request_remove_from_index(SongDocumentManager, instance)


@receiver(post_delete, sender=Lyric)
@receiver(post_save, sender=Lyric)
def sync_song_lyrics_in_index(sender, instance, **kwargs):
    request_update_in_index(SongDocumentManager, instance.song)
