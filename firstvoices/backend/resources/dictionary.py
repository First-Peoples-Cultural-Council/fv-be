from import_export import fields, widgets

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


class DictionaryEntryResource(
    RelatedMediaResourceMixin,
    ControlledSiteContentResource,
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

    def get_or_init_instance(self, instance_loader, row):
        """
        If import job mode = update, update existing entries instead of creating new ones.
        """
        import_job = ImportJob.objects.get(id=self.import_job)
        site = import_job.site
        valid_entry_ids = [
            str(i)
            for i in DictionaryEntry.objects.filter(site=site).values_list(
                "id", flat=True
            )
        ]

        instance_loader.get_instance(row)

        if import_job.mode == ImportJobMode.UPDATE:
            # Skip missing IDs
            if not row.get("id"):
                raise ImportError(f"Missing 'id' for update in row: {row}.")

            # Skip missing types
            if "type" in row and (
                row.get("type") is None or str(row.get("type")).strip() == ""
            ):
                raise ImportError(
                    f"Missing 'type' for update in row with id {row.get('id')}."
                )

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
        return super().get_or_init_instance(instance_loader, row)

    class Meta:
        model = DictionaryEntry
        clean_model_instances = True
        import_id_fields = ["id"]
        skip_unchanged = True
        report_skipped = True
