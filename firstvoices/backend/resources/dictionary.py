import logging

from import_export import fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

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
    DictionaryEntryLink,
    DictionaryEntryRelatedCharacter,
)
from backend.models.media import Audio, Image, Video
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
    related_images = fields.Field(
        column_name="related_images",
        attribute="related_images",
        m2m_add=True,
        widget=ManyToManyWidget(Image, field="id"),
    )
    related_audio = fields.Field(
        column_name="related_audio",
        attribute="related_audio",
        m2m_add=True,
        widget=ManyToManyWidget(Audio, field="id"),
    )
    related_videos = fields.Field(
        column_name="related_videos",
        attribute="related_videos",
        m2m_add=True,
        widget=ManyToManyWidget(Video, field="id"),
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

    def skip_row(self, instance, original, row, import_validation_errors=None):
        # skip rows with non-existent categories
        logger = logging.getLogger(__name__)
        try:
            instance.category = Category.objects.get(id=instance.category.id)
        except Category.DoesNotExist:
            logger.warning(
                f"Skipping row {instance.row_number} because category {instance.category.id} does not exist."
            )
            return True
        return super().skip_row(instance, original, row, import_validation_errors)


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


class DictionaryEntryLinkResource(BaseResource):
    from_dictionary_entry = fields.Field(
        column_name="dictionary_entry",
        attribute="from_dictionary_entry",
        widget=ForeignKeyWidget(DictionaryEntry, "id"),
    )

    to_dictionary_entry = fields.Field(
        column_name="related_entry",
        attribute="to_dictionary_entry",
        widget=ForeignKeyWidget(DictionaryEntry, "id"),
    )

    class Meta:
        model = DictionaryEntryLink

    def skip_row(self, instance, original, row, import_validation_errors=None):
        # skip rows with non-existent "to" dictionary entries
        logger = logging.getLogger(__name__)
        try:
            instance.to_dictionary_entry = DictionaryEntry.objects.get(
                id=instance.to_dictionary_entry.id
            )
        except DictionaryEntry.DoesNotExist:
            logger.warning(
                f"Skipping row {instance.row_number} because entry {instance.to_dictionary_entry.id} does not exist."
            )
            return True
        return super().skip_row(instance, original, row, import_validation_errors)
