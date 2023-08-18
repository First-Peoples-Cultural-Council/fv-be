from import_export import fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from backend.models import (
    Acknowledgement,
    AlternateSpelling,
    Category,
    DictionaryEntry,
    Note,
    PartOfSpeech,
    Pronunciation,
    Translation,
)
from backend.models.constants import Visibility
from backend.resources.base import BaseResource, SiteContentResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class DictionaryEntryResource(SiteContentResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    categories = fields.Field(
        column_name="categories",
        attribute="categories",
        widget=ManyToManyWidget(Category, "id"),
    )

    part_of_speech = fields.Field(
        column_name="part_of_speech",
        attribute="part_of_speech",
        widget=ForeignKeyWidget(PartOfSpeech, "id"),
    )

    class Meta:
        model = DictionaryEntry


class BaseDictionaryEntryContentResource(BaseResource):
    dictionary_entry = fields.Field(
        column_name="dictionary_entry",
        attribute="dictionary_entry",
        widget=ForeignKeyWidget(DictionaryEntry, "id"),
    )

    class Meta:
        abstract = True


class NoteResource(BaseDictionaryEntryContentResource):
    class Meta:
        model = Note


class AcknowledgementResource(BaseDictionaryEntryContentResource):
    class Meta:
        model = Acknowledgement


class TranslationResource(BaseDictionaryEntryContentResource):
    class Meta:
        model = Translation


class AlternateSpellingResource(BaseDictionaryEntryContentResource):
    class Meta:
        model = AlternateSpelling


class PronunciationResource(BaseDictionaryEntryContentResource):
    class Meta:
        model = Pronunciation
