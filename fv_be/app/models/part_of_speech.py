from django.db import models

# FirstVoices
from .base import BaseModel


class PartOfSpeech(BaseModel):
    """Model for Categories."""

    # Fields
    # todo: name for the following field, can we put title ? or will it be very similar to label ?
    # since other models have a title field
    name = models.CharField(max_length=200)
    # from wiki: name of the part of speech in snake case e.g.intransitive_verb
    label = models.CharField(max_length=200)
    # todo: name for the following field
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = "PartsOfSpeech"

    def __str__(self):
        return self.name
