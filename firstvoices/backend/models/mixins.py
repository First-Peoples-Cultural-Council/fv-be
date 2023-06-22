import rules
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext as _

from backend.models import BaseModel
from backend.permissions import predicates


class AuthouredMixin(models.Model):
    """
    Mixin for content having zero or more authours
    """

    class Meta:
        abstract = True

    authours = ArrayField(models.CharField(max_length=200), blank=False, default=list)


class TranslatedText(BaseModel):
    """
    Representing a translation of a string to another language, used by the mixin factory to add `_translations` fields
    to models
    """

    class Meta:
        rules_permissions = {
            "view": rules.always_allow,
            "add": predicates.is_superadmin,
            "change": predicates.is_superadmin,
            "delete": predicates.is_superadmin,
        }
        unique_together = []

    class TranslationLanguages(models.TextChoices):
        # Choices for Language
        ENGLISH = "EN", _("English")
        FRENCH = "FR", _("French")

    text = models.TextField(blank=False)

    language = models.CharField(
        max_length=2,
        choices=TranslationLanguages.choices,
        default=TranslationLanguages.ENGLISH,
    )


def dynamic_translated_field_mixin_factory(
    model_name: str, name: str, blank=True, unique=False, nullable=True
):
    """
    A function that returns a mixin. Used here to generate a "translated" field having both a main text field and also
    a unidirectional one-to-many relationship with TranslatedText

    if you call this with `name` set to  `foo` you'll get a Textfield called `foo` and a relationship `foo_translations`
    added to your model
    """

    class AbstractMixin(models.Model):
        class Meta:
            abstract = True

    AbstractMixin.add_to_class(
        name,
        models.TextField(blank=blank, unique=unique, null=nullable),
    )

    TranslatedText.add_to_class(
        model_name.lower() + "_" + name,
        models.ForeignKey(model_name,
                          on_delete=models.CASCADE,
                          related_name=(name.lower() + "_translations"),
                          null=True
                          )
    )

    return AbstractMixin
