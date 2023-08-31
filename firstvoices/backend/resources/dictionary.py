from import_export import fields
from import_export.results import RowResult
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
    DictionaryEntryLink,
    DictionaryEntryRelatedCharacter,
    TypeOfDictionaryEntry,
)
from backend.resources.base import (
    BaseResource,
    RelatedMediaResourceMixin,
    SiteContentResource,
)
from backend.resources.utils.import_export_widgets import ChoicesWidget


class DictionaryEntryResource(SiteContentResource, RelatedMediaResourceMixin):
    visibility = fields.Field(
        column_name="visibility",
        widget=ChoicesWidget(Visibility.choices),
        attribute="visibility",
    )
    type = fields.Field(
        column_name="type",
        widget=ChoicesWidget(TypeOfDictionaryEntry.choices),
        attribute="type",
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

    def import_row(
        self,
        row,
        instance_loader,
        using_transactions=True,
        dry_run=False,
        raise_errors=None,
        **kwargs,
    ):
        # overriding import_row to ignore errors and skip rows that fail to import without failing the entire import
        # ref: https://github.com/django-import-export/django-import-export/issues/763
        import_result = super().import_row(row, instance_loader, **kwargs)
        if (
            import_result.import_type == RowResult.IMPORT_TYPE_ERROR
            and type(import_result.errors[0].error) == Category.DoesNotExist
        ):
            # Copy the values to display in the preview report
            import_result.diff = [row[val] for val in row]
            # Add a column with the error message
            import_result.diff.append(
                f"Errors: {[err.error for err in import_result.errors]}"
            )
            # clear errors and mark the record to skip
            import_result.errors = []
            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result


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
        report_skipped = True
        model = DictionaryEntryLink

    def import_row(
        self,
        row,
        instance_loader,
        using_transactions=True,
        dry_run=False,
        raise_errors=None,
        **kwargs,
    ):
        # overriding import_row to ignore errors and skip rows that fail to import without failing the entire import
        # ref: https://github.com/django-import-export/django-import-export/issues/763
        import_result = super().import_row(row, instance_loader, **kwargs)
        if (
            import_result.import_type == RowResult.IMPORT_TYPE_ERROR
            and type(import_result.errors[0].error) == DictionaryEntry.DoesNotExist
        ):
            # Copy the values to display in the preview report
            import_result.diff = [row[val] for val in row]
            # Add a column with the error message
            import_result.diff.append(
                f"Errors: {[err.error for err in import_result.errors]}"
            )
            # clear errors and mark the record to skip
            import_result.errors = []
            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result
