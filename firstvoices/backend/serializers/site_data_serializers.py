from collections import OrderedDict
from datetime import datetime

from django.core.paginator import Paginator
from rest_framework import pagination, serializers

from backend.models import Category, Site
from backend.models.dictionary import DictionaryEntry, TypeOfDictionaryEntry
from backend.permissions import utils
from backend.serializers.base_serializers import SiteContentLinkedTitleSerializer


def dict_entry_type_mtd_conversion(type):
    match type:
        case TypeOfDictionaryEntry.WORD:
            return "words"
        case TypeOfDictionaryEntry.PHRASE:
            return "phrases"
        case _:
            return None


class SiteDataSerializer(SiteContentLinkedTitleSerializer):
    config = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    def get_config(self, site):
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
        return config

    def get_data(self, site):
        queryset = (
            site.dictionaryentry_set
            if site is not None and site.dictionaryentry_set is not None
            else None
        )
        request = self.context.get("request")
        serializer = DictionaryEntryDataSerializer(
            queryset, many=True, context={"request": request}
        )

        paginator = DictionaryEntryPaginator()
        paginated_data = paginator.paginate_queryset(
            queryset=serializer.data, request=request
        )
        dictionary_entries = paginator.get_paginated_response(paginated_data)
        return dictionary_entries

    def to_representation(self, instance):
        output = super().to_representation(instance)
        data = output.pop("data", None)
        for key, value in data.items():
            output[key] = value
        return output

    class Meta:
        model = Site
        fields = ("config", "data")


class CategoriesDataSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="title")
    parent_category = serializers.CharField(source="parent")

    class Meta:
        model = Category
        fields = (
            "category",
            "parent_category",
        )


class DictionaryEntryDataSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField()
    entryID = serializers.UUIDField(source="id")
    word = serializers.CharField(source="title")
    definition = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    theme = CategoriesDataSerializer(source="categories", many=True)
    secondary_theme = serializers.SerializerMethodField()
    optional = serializers.SerializerMethodField()
    compare_form = serializers.CharField(source="title")
    sort_form = serializers.SerializerMethodField()
    sorting_form = serializers.SerializerMethodField()

    def get_source(self, dictionaryentry):
        return dict_entry_type_mtd_conversion(dictionaryentry.type)

    def get_definition(self, dictionaryentry):
        if dictionaryentry.translation_set.first() is not None:
            return dictionaryentry.translation_set.first().text
        else:
            return None

    # These are placeholder values and need to be updated when the audio models have been implemented.
    def get_audio(self, dictionaryentry):
        return [
            {
                "speaker": None,
                "filename": "https://v2.dev.firstvoices.com/nuxeo/nxfile/default/136e1a0a-a707-41a9-9ec8-1a4f05b55454"
                "/file:content/TestMP3.mp3",
            }
        ]

    # These are placeholder values and need to be updated when the image models have been implemented.
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
                        "Part of Speech": dictionaryentry.part_of_speech.title,
                    }
                    if dictionaryentry.part_of_speech is not None
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

    def get_sort_form(self, dictionaryentry):
        alphabet_mapper = dictionaryentry.site.alphabet_set.all().first()
        if alphabet_mapper is not None:
            return alphabet_mapper.get_base_form(dictionaryentry.title)
        else:
            return dictionaryentry.title

    def get_sorting_form(self, dictionaryentry):
        alphabet_mapper = dictionaryentry.site.alphabet_set.all().first()
        if alphabet_mapper is not None:
            return alphabet_mapper.get_numerical_sort_form(dictionaryentry.title)
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
    django_paginator_class = Paginator
    page_size = 100

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
