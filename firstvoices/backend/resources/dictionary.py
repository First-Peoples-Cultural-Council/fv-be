import logging

from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models import (
    Acknowledgement,
    AlternateSpelling,
    Category,
    Character,
    DictionaryEntry,
    Note,
    PartOfSpeech,
    Pronunciation,
    Translation,
)
from backend.models.constants import Visibility
from backend.models.dictionary import (
    DictionaryEntryCategory,
    DictionaryEntryRelatedCharacter,
)
from backend.resources.base import BaseResource, SiteContentResource
from backend.resources.utils.import_export_widgets import ChoicesWidget


class DictionaryEntryResource(SiteContentResource):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )

    part_of_speech = fields.Field(
        column_name="part_of_speech",
        attribute="part_of_speech",
        widget=ForeignKeyWidget(PartOfSpeech, "title"),
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


class DictionaryEntryCategoryResource(BaseResource):
    dictionary_entry = fields.Field(
        column_name="dictionary_entry",
        attribute="dictionary_entry",
        widget=ForeignKeyWidget(DictionaryEntry, "id"),
    )

    category = fields.Field(
        column_name="category",
        attribute="category",
        widget=ForeignKeyWidget(Category, "id"),
    )

    class Meta:
        model = DictionaryEntryCategory

    def before_import_row(self, row, **kwargs):
        # Skip rows with categories that don't exist
        logger = logging.getLogger(__name__)

        try:
            Category.objects.get(id=row["category"])
        except Category.DoesNotExist:
            logger.warning(
                f"Skipping row with category id {row['category']} because it does not exist"
            )
            raise self.skip_row("Category does not exist")


class DictionaryEntryRelatedCharacterResource(BaseResource):
    character = fields.Field(
        column_name="character",
        attribute="character",
        widget=ForeignKeyWidget(Character, "id"),
    )
    dictionary_entry = fields.Field(
        column_name="dictionary_entry",
        attribute="dictionary_entry",
        widget=ForeignKeyWidget(DictionaryEntry, "id"),
    )

    class Meta:
        model = DictionaryEntryRelatedCharacter
