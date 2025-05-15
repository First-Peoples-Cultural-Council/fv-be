import logging
import uuid

import nh3
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from rules.contrib.models import RulesModel

from backend.models.constants import DEFAULT_TITLE_LENGTH
from backend.permissions.managers import PermissionFilterMixin, PermissionsManager
from backend.utils.character_utils import clean_input

from .constants import Visibility


class BaseModel(PermissionFilterMixin, RulesModel):
    """
    Base model for all FirstVoices Backend models, with standard fields and support for rules-based permissions.

    Date field values are generated automatically, but user fields (created_by and last_modified_by) are required when
    creating new data.

    Access rules can be configured using a declaration in the Meta class, like this example:
    class Meta:
        rules_permissions = {
            "add": rules.is_staff,
            "view": rules.is_authenticated,
        }
    See the django-rules docs [https://github.com/dfunckt/django-rules#permissions-in-models] for more details.
    """

    class Meta:
        abstract = True

    # The permission manager adds methods for accessing only the items that the user has permission to view
    objects = PermissionsManager()

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )

    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="created_%(app_label)s_%(class)s",
    )

    created = models.DateTimeField(default=timezone.now, db_index=True)

    last_modified_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="modified_%(app_label)s_%(class)s",
    )

    last_modified = models.DateTimeField(default=timezone.now, db_index=True)

    system_last_modified_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        default=None,
        related_name="system_modified_%(app_label)s_%(class)s",
    )

    system_last_modified = models.DateTimeField(default=timezone.now, db_index=True)

    logger = logging.getLogger(__name__)

    def save(self, set_modified_date=True, *args, **kwargs):
        self.system_last_modified = timezone.now()
        """Update last_modified time if updating the model."""
        if (not self._state.adding) and set_modified_date:
            self.last_modified = timezone.now()
        return super().save(*args, **kwargs)


class BaseSiteContentModel(BaseModel):
    """
    Base model for non-access-controlled site content data such as categories, that do not have their own
    visibility levels. Can also be used as a base for more specific types of site content base models.
    """

    class Meta:
        abstract = True

    site = models.ForeignKey(
        to="backend.Site", on_delete=models.CASCADE, related_name="%(class)s_set"
    )


class BaseControlledSiteContentModel(BaseSiteContentModel):
    """
    Base model for access-controlled site content models such as words, phrases, songs, and stories, that have their own
    visibility level setting.
    """

    class Meta:
        abstract = True

    visibility = models.IntegerField(
        choices=Visibility.choices, default=Visibility.TEAM, db_index=True
    )


# method to add last_modified and created fields if missing in the data, helpful for fixtures
@receiver(pre_save, sender="backend.PartOfSpeech")
@receiver(pre_save, sender="backend.appjson")
@receiver(pre_save, sender="backend.languagefamily")
@receiver(pre_save, sender="backend.language")
def pre_save_for_fixtures(sender, instance, **kwargs):
    if kwargs["raw"]:
        if not instance.created:
            instance.created = timezone.now()
        instance.last_modified = timezone.now()


class TruncatingCharField(models.CharField):
    """
    Custom CharField which auto truncates the value if it goes above the max_length.
    Strips any whitespace in the beginning or in the end before enforcing max length.
    Ref: https://docs.djangoproject.com/en/4.2/ref/models/fields/#django.db.models.Field.get_prep_value
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value:
            return value.strip()[: self.max_length]
        return value


class SanitizedHtmlField(models.TextField):
    """
    Custom TextField that automatically cleans HTML content using the nh3 library.
    Content that is not HTML remains unchanged.
    """

    def to_python(self, value):
        value = super().to_python(value)
        if value not in self.empty_values and nh3.is_html(value):
            value = nh3.clean(value)
        return value


class AudienceMixin(models.Model):
    class Meta:
        abstract = True

    exclude_from_games = models.BooleanField(default=False)
    exclude_from_kids = models.BooleanField(default=False)


class TranslatedTitleMixin(models.Model):
    class Meta:
        abstract = True

    title = models.CharField(max_length=DEFAULT_TITLE_LENGTH, blank=False, null=False)
    title_translation = models.CharField(
        max_length=DEFAULT_TITLE_LENGTH, blank=True, null=False
    )

    def save(self, *args, **kwargs):
        self.title = clean_input(self.title)
        self.title_translation = clean_input(self.title_translation)
        return super().save(*args, **kwargs)


class TranslatedIntroMixin(models.Model):
    class Meta:
        abstract = True

    introduction = SanitizedHtmlField(blank=True, null=False)
    introduction_translation = SanitizedHtmlField(blank=True, null=False)

    def save(self, *args, **kwargs):
        self.introduction = clean_input(self.introduction)
        self.introduction_translation = clean_input(self.introduction_translation)
        return super().save(*args, **kwargs)


class TranslatedTextMixin(models.Model):
    class Meta:
        abstract = True

    text = SanitizedHtmlField(blank=False)
    translation = SanitizedHtmlField(blank=True)

    def save(self, *args, **kwargs):
        self.text = clean_input(self.text)
        self.translation = clean_input(self.translation)
        return super().save(*args, **kwargs)
