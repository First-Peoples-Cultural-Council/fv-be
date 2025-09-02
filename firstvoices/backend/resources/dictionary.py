from import_export import fields
from import_export.widgets import ForeignKeyWidget

from backend.models import Category, DictionaryEntry, ImportJob
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
    ControlledSiteContentResource,
    RelatedMediaResourceMixin,
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

    # Related entries
    related_dictionary_entries = fields.Field(
        column_name="related_entry",
        attribute="related_dictionary_entries",
        widget=CustomManyToManyWidget(
            model=DictionaryEntry, column_name="related_entry"
        ),
    )

    import_job = fields.Field(
        column_name="import_job",
        attribute="import_job",
        widget=ForeignKeyWidget(ImportJob),
    )

    external_system = fields.Field(
        column_name="external_system",
        attribute="external_system",
        widget=ForeignKeyWidget(ExternalDictionaryEntrySystem, field="title"),
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

    class Meta:
        model = DictionaryEntry
        clean_model_instances = True
