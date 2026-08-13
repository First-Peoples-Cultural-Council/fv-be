from import_export import fields, widgets
from import_export.results import RowResult

from backend.models import Category, DictionaryEntry, ImportJob, ImportJobMode
from backend.models.constants import Visibility
from backend.models.dictionary import (
    ExternalDictionaryEntrySystem,
    TypeOfDictionaryEntry,
)
from backend.resources.base import (
    ControlledSiteContentResource,
    RelatedMediaResourceMixin,
)
from backend.resources.utils.import_export_widgets import (
    ChoicesWidget,
    CustomManyToManyWidget,
    InvertedBooleanFieldWidget,
    PartOfSpeechWidget,
    TextListWidget,
)
from backend.utils.character_utils import clean_input


class DictionaryEntryResource(
    RelatedMediaResourceMixin,
    ControlledSiteContentResource,
):
    type = fields.Field(
        column_name="type",
        widget=ChoicesWidget(
            TypeOfDictionaryEntry.choices,
        ),
        attribute="type",
    )
    part_of_speech = fields.Field(
        column_name="part_of_speech",
        attribute="part_of_speech",
        widget=PartOfSpeechWidget(),
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

    related_dictionary_entries_by_id = fields.Field(
        column_name="related_entry_ids",
        attribute="related_dictionary_entries",
        m2m_add=True,
        widget=widgets.ManyToManyWidget(DictionaryEntry, separator=",", field="id"),
    )

    import_job = fields.Field(
        column_name="import_job",
        attribute="import_job",
        widget=widgets.ForeignKeyWidget(ImportJob),
    )

    external_system = fields.Field(
        column_name="external_system",
        attribute="external_system",
        widget=widgets.ForeignKeyWidget(ExternalDictionaryEntrySystem, field="title"),
    )

    exclude_from_games = fields.Field(
        column_name="include_in_games",
        attribute="exclude_from_games",
        widget=InvertedBooleanFieldWidget(column="include_in_games", default=False),
    )
    exclude_from_kids = fields.Field(
        column_name="include_on_kids_site",
        attribute="exclude_from_kids",
        widget=InvertedBooleanFieldWidget(column="include_on_kids_site", default=False),
    )

    def __init__(
        self,
        missing_uploaded_media=None,
        missing_referenced_media=None,
        missing_entries=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if missing_uploaded_media is None:
            missing_uploaded_media = []
        if missing_referenced_media is None:
            missing_referenced_media = []
        if missing_entries is None:
            missing_entries = []
        self.missing_uploaded_media = missing_uploaded_media
        self.missing_referenced_media = missing_referenced_media
        self.missing_entries = missing_entries

        # create missing related content error lookup
        self.missing_content_errors = {}
        for obj in missing_uploaded_media:
            self.missing_content_errors.setdefault(obj["idx"], []).append(
                f"Media file missing in uploaded files: "
                f"{obj['filename']}, column: {obj['column']}."
            )
        for obj in missing_referenced_media:
            self.missing_content_errors.setdefault(obj["idx"], []).append(
                "Referenced media not found for "
                f"ID: {obj['id']} in column: {obj['column']}."
            )
        for obj in missing_entries:
            self.missing_content_errors.setdefault(obj["idx"], []).append(
                f"Referenced dictionary entry not found for ID: {obj['id']} in column: 'related_entry_ids'."
            )

        self._current_row_number = None
        self._processed_ids = set()

    def before_import_row(self, row, **kwargs):
        title = row.get("title")
        if title:
            cleaned_title = clean_input(title)
            row["title"] = cleaned_title

    def import_row(self, row, instance_loader, **kwargs):
        row_number = kwargs.get("row_number")
        self._current_row_number = row_number

        # return individual error messages for missing content if missing content errors are present
        result = super().import_row(row, instance_loader, **kwargs)
        if (
            result.import_type == RowResult.IMPORT_TYPE_SKIP
            and row_number in self.missing_content_errors
        ):
            result.error_messages = list(self.missing_content_errors[row_number])

        return result

    def get_or_init_instance(self, instance_loader, row):
        """
        Raise errors depending on import job type and row data (missing related content, visibility restrictions, etc.)
        before initializing the instance.
        """
        missing_content_errors = self.missing_content_errors.get(
            self._current_row_number
        )
        if missing_content_errors:
            # raise an error and allow the import_row() method to add each individual error
            raise ImportError()

        instance_loader.get_instance(row)
        import_job = ImportJob.objects.get(id=self.import_job)
        site = import_job.site

        # Raise errors for invalid type/visibility
        self.raise_invalid_value_errors(row)

        # Raise errors for update data
        if import_job.mode == ImportJobMode.UPDATE:
            self.raise_row_update_errors(row, site)

        return super().get_or_init_instance(instance_loader, row)

    def save_m2m(self, instance, row, **kwargs):
        super().save_m2m(instance, row, **kwargs)

        # Override to replace existing M2M relations
        m2m_field_map = {
            "related_entry_ids": "related_dictionary_entries",
            "related_audio": "related_audio",
            "related_images": "related_images",
            "related_videos": "related_videos",
            "related_documents": "related_documents",
        }

        for data_field, instance_field in m2m_field_map.items():
            if data_field in row:
                new_values = row[data_field].split(",")
                new_values = [value.strip() for value in new_values if value]
                getattr(instance, instance_field).set(new_values)

    def raise_row_update_errors(self, row, site):
        valid_entry_ids = [
            str(i)
            for i in DictionaryEntry.objects.filter(site=site).values_list(
                "id", flat=True
            )
        ]

        # Skip missing IDs
        if not row.get("id"):
            raise ImportError(f"Missing 'id' for update in row: {row}.")

        # Enforce visibility restrictions
        if (
            row.get("visibility")
            and Visibility[row.get("visibility").upper().strip()].value
            > site.visibility
        ):
            raise ImportError(
                f"Cannot update entry with id {row.get('id')} due to visibility restrictions."
            )

        # Ensure updated entries belong to the site
        if row.get("id") not in valid_entry_ids:
            raise ImportError(
                f"Entry with id {row.get('id')} does not belong to site '{site.title}'."
            )

        # Prevent duplicate updates within the same import
        if str(row.get("id")) in self._processed_ids:
            raise ImportError(
                f"Duplicate entry with id {row.get('id')} found in import."
            )
        self._processed_ids.add(str(row.get("id")))

    @staticmethod
    def raise_invalid_value_errors(row):
        if "type" in row and (
            str(row["type"]).strip().lower() not in TypeOfDictionaryEntry.values
            and row["type"]
        ):
            raise ImportError(
                f"Invalid value '{row['type']}' in type column. Expected one of: {TypeOfDictionaryEntry.values}."
            )

        visibility_values = [v.lower() for v in Visibility.labels]

        if "visibility" in row and (
            str(row["visibility"]).strip().lower() not in visibility_values
            and row["visibility"]
        ):
            raise ImportError(
                f"Invalid value '{row['visibility']}' in visibility column. Expected one of: {visibility_values}."
            )

    class Meta:
        model = DictionaryEntry
        clean_model_instances = True
        import_id_fields = ["id"]
        skip_unchanged = True
        report_skipped = True
        use_bulk = False
