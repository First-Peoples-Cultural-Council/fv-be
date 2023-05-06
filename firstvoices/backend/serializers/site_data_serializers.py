from collections import OrderedDict
from datetime import datetime

from rest_framework import pagination, serializers

from backend.models import Category, Site
from backend.models.dictionary import DictionaryEntry
from backend.predicates import utils
from backend.serializers.base_serializers import SiteContentLinkedTitleSerializer


def dict_entry_type_mtd_conversion(type):
    match type:
        case DictionaryEntry.TypeOfDictionaryEntry.WORD:
            return "words"
        case DictionaryEntry.TypeOfDictionaryEntry.PHRASE:
            return "phrases"
        case _:
            return None


class SiteDataSerializer(SiteContentLinkedTitleSerializer):
    site_data_export = serializers.SerializerMethodField()

    def get_site_data_export(self, site):
        request = self.context.get("request")
        characters_list = [
            character
            for character in utils.filter_by_viewable(
                request.user, site.character_set.all()
            ).order_by("sort_order")
        ]
        config = {
            "L1": {
                "name": None if site is None else site.title,
                "lettersInLanguage": [character.title for character in characters_list],
                "transducers": {},
            },
            "L2": {"name": "English"},
            "build": datetime.now().strftime("%Y%m%d%H%M"),
        }

        queryset = site.dictionaryentry_set
        request = self.context.get("request")
        serializer = DictionaryEntryDataSerializer(
            queryset, many=True, context={"request": request}
        )

        paginator = DictionaryEntryPaginator()
        paginated_data = paginator.paginate_queryset(
            queryset=serializer.data, request=request
        )
        dictionary_entries = paginator.get_paginated_response(paginated_data)

        return {"config": config, "paginatedDictionaryData": dictionary_entries}

    class Meta:
        model = Site
        fields = ("site_data_export",)


class CategoriesDataSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    parent_category = serializers.SerializerMethodField()

    def get_category(self, category):
        return category.title

    def get_parent_category(self, category):
        if category.parent is not None:
            return category.parent.title
        else:
            return None

    class Meta:
        model = Category
        fields = (
            "category",
            "parent_category",
        )


class DictionaryEntryDataSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField()
    entryID = serializers.SerializerMethodField()
    word = serializers.SerializerMethodField()
    definition = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    theme = CategoriesDataSerializer(source="categories", many=True)
    secondary_theme = serializers.SerializerMethodField()
    optional = serializers.SerializerMethodField()
    compare_form = serializers.SerializerMethodField()
    sort_form = serializers.SerializerMethodField()
    sorting_form = serializers.SerializerMethodField()

    def get_source(self, dictionaryentry):
        return dict_entry_type_mtd_conversion(dictionaryentry.type)

    def get_entryID(self, dictionaryentry):
        return dictionaryentry.id

    def get_word(self, dictionaryentry):
        return dictionaryentry.title

    def get_definition(self, dictionaryentry):
        if dictionaryentry.translation_set.first() is not None:
            return dictionaryentry.translation_set.first().text
        else:
            return None

    def get_audio(self, dictionaryentry):
        return [
            {
                "speaker": None,
                "filename": "https://v2.dev.firstvoices.com/nuxeo/nxfile/default/136e1a0a-a707-41a9-9ec8-1a4f05b55454"
                "/file:content/TestMP3.mp3",
            }
        ]

    def get_img(self, dictionaryentry):
        return (
            "https://v2.dev.firstvoices.com/nuxeo/nxfile/default/5c9eef16-4665-40b9-89ce-debc0301f93b/file:content"
            "/pexels-stijn-dijkstra-2583852.jpg"
        )

    def get_secondary_theme(self, dictionaryentry):
        return None

    def get_optional(self, dictionaryentry):
        return (
            {
                **(
                    {
                        "Reference": dictionaryentry.acknowledgement_set.first().text,
                    }
                    if dictionaryentry.acknowledgement_set.first() is not None
                    else {}
                ),
                **(
                    {
                        "Part of Speech": dictionaryentry.translation_set.first().part_of_speech.title,
                    }
                    if dictionaryentry.translation_set.first() is not None
                    and dictionaryentry.translation_set.first().part_of_speech
                    is not None
                    else {}
                ),
                **(
                    {
                        "Note": dictionaryentry.note_set.first().text,
                    }
                    if dictionaryentry.note_set.first() is not None
                    else {}
                ),
            },
        )

    def get_compare_form(self, dictionaryentry):
        return dictionaryentry.title

    def get_sort_form(self, dictionaryentry):
        request = self.context.get("request")
        alphabet_mapper = utils.filter_by_viewable(
            request.user, dictionaryentry.site.alphabet_set.all()
        ).first()
        if alphabet_mapper is not None:
            return alphabet_mapper.get_sort_form(dictionaryentry.title)
        else:
            return dictionaryentry.title

    def get_sorting_form(self, dictionaryentry):
        request = self.context.get("request")
        alphabet_mapper = utils.filter_by_viewable(
            request.user, dictionaryentry.site.alphabet_set.all()
        ).first()
        if alphabet_mapper is not None:
            sort_form = alphabet_mapper.get_sort_form(dictionaryentry.title)
            return alphabet_mapper.get_numerical_sort_form(sort_form)
        else:
            return dictionaryentry.title

    class Meta:
        model = DictionaryEntry
        fields = (
            "source",
            "entryID",
            "word",
            "definition",
            "audio",
            "img",
            "theme",
            "secondary_theme",
            "optional",
            "compare_form",
            "sort_form",
            "sorting_form",
        )


class DictionaryEntryPaginator(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return OrderedDict(
            [
                ("count", self.page.paginator.count),
                ("pages", self.page.paginator.num_pages),
                ("pageSize", self.get_page_size(self.request)),
                (
                    "next",
                    self.page.next_page_number() if self.page.has_next() else None,
                ),
                ("next_url", self.get_next_link()),
                (
                    "previous",
                    self.page.previous_page_number()
                    if self.page.has_previous()
                    else None,
                ),
                ("previous_url", self.get_previous_link()),
                ("data", data),
            ]
        )
