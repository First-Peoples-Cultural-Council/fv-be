import logging
import uuid

from django.db import models

from fv_be.users.models import User

logger = logging.getLogger(__name__)

ROLE_CHOICES = (
    ("member", "MEMBER"),
    ("recorder", "RECORDER"),
    ("editor", "EDITOR"),
    ("language_admin", "LANGUAGE_ADMIN"),
)

STATE_CHOICES = (
    ("disabled", "DISABLED"),
    ("enabled", "ENABLED"),
    ("new", "NEW"),
    ("published", "PUBLISHED"),
    ("republish", "REPUBLISH"),
)


class Site(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    state = models.CharField(max_length=9, choices=STATE_CHOICES, default="new")

    # logo
    # banner
    # url_slug
    # site_visibility

    def __str__(self):
        return self.title


class Role(models.Model):
    # todo: best way to do a limited list?
    name = models.CharField(max_length=25, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("site", "user")


# ----------------------------------------------------------------------------------------------------------------------
# Testing Code Below
# ----------------------------------------------------------------------------------------------------------------------
# A model for a word containing a foreign key to a language
class Word(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    state = models.CharField(max_length=9, choices=STATE_CHOICES, default="new")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self._state.adding is True
        super().save(*args, **kwargs)

        if is_new:
            logger.debug(f'Created a new word "{self.title}" ID: {self.id}')


# A model for a category containing a foreign key to a language
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    words = models.ManyToManyField(Word, related_name="words", blank=True)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"

    @property
    def state(self):
        return self.site.state

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self._state.adding is True
        super().save(*args, **kwargs)

        if is_new:
            logger.debug(f'Created a new category "{self.title}" ID: {self.id}')
