import uuid

from import_export import fields
from import_export.results import RowResult

from backend.models import Category, DictionaryEntry, PartOfSpeech
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.resources.base import (
    AudienceMixin,
    ControlledSiteContentResource,
    RelatedMediaResourceMixin,
)
from backend.resources.utils.import_export_widgets import (
    ChoicesWidget,
    CleanForeignKeyWidget,
    CustomManyToManyWidget,
    TextListWidget,
)


class DictionaryEntryResource(
    AudienceMixin, ControlledSiteContentResource, RelatedMediaResourceMixin
):
    type = fields.Field(
        column_name="type",
        widget=ChoicesWidget(
            TypeOfDictionaryEntry.choices, default=TypeOfDictionaryEntry.WORD
        ),
        attribute="type",
    )
    part_of_speech = fields.Field(
        column_name="part_of_speech",
        attribute="part_of_speech",
        widget=CleanForeignKeyWidget(PartOfSpeech, "title", title_case=True),
    )
    categories = fields.Field(
        column_name="category",
        attribute="categories",
        m2m_add=True,
        widget=CustomManyToManyWidget(
            model=Category, field="title", column_name="category"
        ),
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
        column_name="alternate_spelling",
        attribute="alternate_spellings",
        m2m_add=True,
        widget=TextListWidget(prefix="alternate_spelling"),
    )

    # Related entries
    related_dictionary_entries = fields.Field(
        column_name="related_entry",
        attribute="related_dictionary_entries",
        widget=CustomManyToManyWidget(
            model=DictionaryEntry, column_name="related_entry"
        ),
    )

    def __init__(self, site=None, run_as_user=None):
        self.site = site
        self.run_as_user = run_as_user

    def before_import(self, dataset, **kwargs):
        # Adding required columns, since these will not be present in the headers
        dataset.append_col(lambda x: str(uuid.uuid4()), header="id")
        dataset.append_col(lambda x: str(self.site.id), header="site")
        dataset.append_col(lambda x: str(self.run_as_user), header="created_by")
        dataset.append_col(lambda x: str(self.run_as_user), header="last_modified_by")

    def import_row(self, row, instance_loader, **kwargs):
        # Marking erroneous and invalid rows as skipped, then clearing the errors and validation_errors
        # so the valid rows can be imported
        import_result = super().import_row(row, instance_loader, **kwargs)
        if import_result.import_type in [
            RowResult.IMPORT_TYPE_ERROR,
            RowResult.IMPORT_TYPE_INVALID,
        ]:
            import_result.error_messages = []  # custom field to store messages
            import_result.number = kwargs["row_number"]

            if import_result.errors:
                import_result.error_messages = [
                    str(err.error).split("\n")[0] for err in import_result.errors
                ]
                import_result.errors = []

            if import_result.validation_error:
                import_result.error_messages = [
                    err for err in import_result.validation_error.messages
                ]
                import_result.validation_error = None

            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result

    class Meta:
        model = DictionaryEntry
        clean_model_instances = True
