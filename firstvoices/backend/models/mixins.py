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

    We need to pass in the model name because `self` is not accessible at class scope

    TranslatedText will get an FK to the model you provide since Django does not support true OneToMany, only ManyToOne
    (meaning essentially that TranslatedText "owns" the relationship, which is semantically not precisely what we want).

    This can also be solved with ManyToMany relationships to change it from a "one table with lots of columns" problem
    to a "lots of join tables with two columns" problem. Set a unique constraint for each one on the translation side to
    simulate ManyToOne. Adding items becomes more cumbersome.

    It might also be possible to use an HStoreField here, and constrain keys to EN and FR, though validation becomes
    tricky and it doesn't work smoothly in the admin interface.
    """

    class AbstractMixin(models.Model):
        class Meta:
            abstract = True

    # add a plain text field to ourselves
    AbstractMixin.add_to_class(
        name,
        models.TextField(blank=blank, unique=unique, null=nullable),
    )

    # and add an FK from TranslatedText back to ourselves, with a sensible related_name
    TranslatedText.add_to_class(
        model_name.lower() + "_" + name,
        models.ForeignKey(model_name,
                          on_delete=models.CASCADE,
                          related_name=(name.lower() + "_translations"),
                          null=True  # Must be nullable due to creation-order by admin page
                          )
    )

    return AbstractMixin
