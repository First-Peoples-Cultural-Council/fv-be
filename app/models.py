import uuid
import logging

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from .rules import *

logger = logging.getLogger(__name__)

STATE_CHOICES = (
    ('disabled', 'DISABLED'),
    ('enabled', 'ENABLED'),
    ('new', 'NEW'),
    ('published', 'PUBLISHED'),
    ('republish', 'REPUBLISH'),
)


# A model for a language
class Language(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    state = models.CharField(max_length=9, choices=STATE_CHOICES, default='new')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self._state.adding is True
        super(Language, self).save(*args, **kwargs)

        if is_new:
            logger.debug(f"Created a new language \"{self.title}\" ID: {self.id}")


# A model for a word containing a foreign key to a language
class Word(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    state = models.CharField(max_length=9, choices=STATE_CHOICES, default='new')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self._state.adding is True
        super(Word, self).save(*args, **kwargs)

        if is_new:
            logger.debug(f"Created a new word \"{self.title}\" ID: {self.id}")


# A model for a phrase containing a foreign key to a language
class Phrase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    state = models.CharField(max_length=9, choices=STATE_CHOICES, default='new')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self._state.adding is True
        super(Phrase, self).save(*args, **kwargs)

        if is_new:
            logger.debug(f"Created a new phrase \"{self.title}\" ID: {self.id}")


# On language delete perform some cleanup tasks.
@receiver(post_delete, sender=Language)
def cleanup_language(sender, instance, **kwargs):
    # Cleanup groups
    deleted_count = Group.objects.filter(name=f'{instance.title}_member').delete()
    if deleted_count == 0:
        logger.error(f"Member group could not be deleted for {instance.title} language")
    deleted_count = Group.objects.filter(name=f'{instance.title}_recorder').delete()
    if deleted_count == 0:
        logger.error(f"Recorder group could not be deleted for {instance.title} language")
    deleted_count = Group.objects.filter(name=f'{instance.title}_editor').delete()
    if deleted_count == 0:
        logger.error(f"Editor group could not be deleted for {instance.title} language")
    deleted_count = Group.objects.filter(name=f'{instance.title}_language_admin').delete()
    if deleted_count == 0:
        logger.error(f"Language Administrator group could not be deleted for {instance.title} language")


# Update the language group names if the language title changes
@receiver(pre_save, sender=Language)
def check_for_state_update(sender, instance, **kwargs):
    try:
        old_instance = sender.objects.get(id=instance.id)
    except sender.DoesNotExist:
        return None

    if old_instance.title != instance.title:
        Group.objects.filter(name=f'{old_instance.title}_member').update(name=f'{instance.title}_member')
        Group.objects.filter(name=f'{old_instance.title}_recorder').update(name=f'{instance.title}_recorder')
        Group.objects.filter(name=f'{old_instance.title}_editor').update(name=f'{instance.title}_editor')
        Group.objects.filter(name=f'{old_instance.title}_language_admin').update(
            name=f'{instance.title}_language_admin')


# Add group permissions to the model instance if it freshly created
@receiver(post_save, sender=Language)
def update_m2m_relationships(sender, instance, created, **kwargs):
    if created:
        language = instance.title
        Group.objects.get_or_create(name=f'{language}_member')
        Group.objects.get_or_create(name=f'{language}_recorder')
        Group.objects.get_or_create(name=f'{language}_editor')
        Group.objects.get_or_create(name=f'{language}_language_admin')
