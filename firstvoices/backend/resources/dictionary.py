import uuid

from import_export import fields
from import_export.results import RowResult
from import_export.widgets import ForeignKeyWidget

from backend.models import Category, Character, DictionaryEntry, PartOfSpeech
from backend.models.dictionary import (
    DictionaryEntryCategory,
    DictionaryEntryLink,
    DictionaryEntryRelatedCharacter,
    TypeOfDictionaryEntry,
)
from backend.resources.base import (
    AudienceMixin,
    BaseResource,
    ControlledSiteContentResource,
    RelatedMediaResourceMixin,
)
from backend.resources.utils.import_export_widgets import ChoicesWidget, TextListWidget


class DictionaryEntryResource(
    AudienceMixin, ControlledSiteContentResource, RelatedMediaResourceMixin
):
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
    # Text List attributes
    translations = fields.Field(
        column_name="translation",
        attribute="translations",
        widget=TextListWidget(prefix="translation"),
    )
    acknowledgements = fields.Field(
        column_name="acknowledgement",
        attribute="acknowledgements",
        widget=TextListWidget(prefix="acknowledgement"),
    )
    notes = fields.Field(
        column_name="note", attribute="notes", widget=TextListWidget(prefix="note")
    )
    pronunciations = fields.Field(
        column_name="pronunciation",
        attribute="pronunciations",
        widget=TextListWidget(prefix="pronunciation"),
    )
    alternate_spellings = fields.Field(
        column_name="alt_spelling",
        attribute="alternate_spellings",
        widget=TextListWidget(prefix="alt_spelling"),
    )

    def __init__(self, site=None):
        if site:
            self.site = site

    def before_import(self, dataset, **kwargs):
        if "id" not in dataset.headers:
            dataset.append_col(lambda x: str(uuid.uuid4()), header="id")
        if "site" not in dataset.headers:
            dataset.append_col(lambda x: str(self.site.id), header="site")

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
