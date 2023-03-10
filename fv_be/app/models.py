import logging
import uuid

import rules
from django.db import models
from rules.contrib.models import RulesModel

from fv_be.users.models import User

from . import predicates

logger = logging.getLogger(__name__)

ROLE_CHOICES = (
    ("member", "MEMBER"),
    ("recorder", "RECORDER"),
    ("editor", "EDITOR"),
    ("language_admin", "LANGUAGE_ADMIN"),
)

STATE_CHOICES = (
    ("new", "Team-only"),
    ("enabled", "Members-only"),
    ("published", "Public"),
)


class Site(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    state = models.CharField(max_length=9, choices=STATE_CHOICES, default="new")
    # logo
    # banner
    # url_slug

    class Meta:
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,
            "change": predicates.is_at_least_language_admin,
            "delete": predicates.is_superadmin,
        }

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

    def __str__(self):
        return f"{self.site} / {self.user} / {self.role}"


# ----------------------------------------------------------------------------------------------------------------------
# Testing Code Below
# ----------------------------------------------------------------------------------------------------------------------
# A model for a word containing a foreign key to a language
class Word(RulesModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    state = models.CharField(max_length=9, choices=STATE_CHOICES, default="new")

    class Meta:
        # these permissions could be defined on a base class for access-controlled site content
        rules_permissions = {
            "view": predicates.is_visible_object,
            "add": predicates.is_at_least_recorder,
            "change": predicates.is_at_least_editor,
            "delete": predicates.is_at_least_language_admin,
        }

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self._state.adding is True
        super().save(*args, **kwargs)

        if is_new:
            logger.debug(f'Created a new word "{self.title}" ID: {self.id}')


# A model for a category containing a foreign key to a language
class Category(RulesModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    words = models.ManyToManyField(Word, related_name="words", blank=True)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"

        # these permissions could be defined on a base class for non-access-controlled site content
        rules_permissions = {
            "view": predicates.is_visible_site,
            "add": predicates.is_at_least_language_admin,
            "change": predicates.is_at_least_language_admin,
            "delete": predicates.is_at_least_language_admin,
        }

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
