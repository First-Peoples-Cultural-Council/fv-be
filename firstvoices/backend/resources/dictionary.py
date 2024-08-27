import uuid

from import_export import fields

from backend.models import DictionaryEntry, PartOfSpeech
from backend.models.dictionary import TypeOfDictionaryEntry
from backend.resources.base import (
    AudienceMixin,
    ControlledSiteContentResource,
    RelatedMediaResourceMixin,
)
from backend.resources.utils.import_export_widgets import (
    CategoryWidget,
    ChoicesWidget,
    CleanForeignKeyWidget,
    RelatedEntriesWidget,
    TextListWidget,
)


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
        widget=CleanForeignKeyWidget(PartOfSpeech, "title", title_case=True),
    )
    categories = fields.Field(
        column_name="category",
        attribute="categories",
        m2m_add=True,
        widget=CategoryWidget(),
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
        widget=TextListWidget(prefix="alternate_spelling"),
    )

    # Related entries
    related_dictionary_entries = fields.Field(
        column_name="related_entry",
        attribute="related_dictionary_entries",
        widget=RelatedEntriesWidget(),
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
