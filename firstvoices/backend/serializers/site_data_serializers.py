from collections import OrderedDict
from datetime import datetime

from django.core.paginator import Paginator
from rest_framework import pagination, serializers

from backend.models import Category, Site
from backend.models.dictionary import DictionaryEntry, TypeOfDictionaryEntry
from backend.models.media import Audio, Image
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


class CategoriesDataSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="title")
    parent_category = serializers.CharField(source="parent")

    class Meta:
        model = Category
        fields = (
            "category",
            "parent_category",
        )


class SiteDataSerializer(SiteContentLinkedTitleSerializer):
    config = serializers.SerializerMethodField()
    categories = CategoriesDataSerializer(source="category_set", many=True)

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

    class Meta:
        model = Site
        fields = (
            "config",
            "categories",
        )


class AudioDataSerializer(serializers.ModelSerializer):
    speaker = serializers.SerializerMethodField()
    filename = serializers.FileField(source="original.content")

    @staticmethod
    def get_speaker(audio):
        speakers = audio.speakers.all()
        name = speakers[0].name if speakers.count() > 0 else None
        return name

    class Meta:
        model = Audio
        fields = (
            "speaker",
            "filename",
        )


class ImageDataSerializer(serializers.ModelSerializer):
    filename = serializers.FileField(source="original.content")

    class Meta:
        model = Image
        fields = ("filename",)


class DictionaryEntryDataSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField()
    entryID = serializers.UUIDField(source="id")
    word = serializers.CharField(source="title")
    definition = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    theme = serializers.SerializerMethodField()
    secondary_theme = serializers.SerializerMethodField()
    optional = serializers.SerializerMethodField()
    compare_form = serializers.CharField(source="title")
    sort_form = serializers.SerializerMethodField()
    sorting_form = serializers.SerializerMethodField()

    @staticmethod
    def get_source(dictionaryentry):
        return dict_entry_type_mtd_conversion(dictionaryentry.type)

    @staticmethod
    def get_definition(dictionaryentry):
        if dictionaryentry.translation_set.count() > 0:
            return dictionaryentry.translation_set.all()[0].text
        else:
            return None

    @staticmethod
    def get_audio(dictionaryentry):
        return AudioDataSerializer(dictionaryentry.related_audio, many=True).data

    @staticmethod
    def get_img(dictionaryentry):
        return ImageDataSerializer(dictionaryentry.related_images, many=True).data

    @staticmethod
    def get_theme(dictionaryentry):
        return [
            entry.title
            for entry in dictionaryentry.categories.all()
            if entry.parent is None
        ]

    @staticmethod
    def get_secondary_theme(dictionaryentry):
        return [
            entry.title
            for entry in dictionaryentry.categories.all()
            if entry.parent is not None
        ]

    @staticmethod
    def get_optional(dictionaryentry):
        return (
            {
                **(
                    {
                        "Reference": dictionaryentry.acknowledgement_set.all()[0].text,
                    }
                    if dictionaryentry.acknowledgement_set.count() > 0
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
                        "Note": dictionaryentry.note_set.all()[0].text,
                    }
                    if dictionaryentry.note_set.count() > 0
                    else {}
                ),
            },
        )

    @staticmethod
    def get_sort_form(dictionaryentry):
        alphabet_mapper = dictionaryentry.site.alphabet_set.all()[0]
        if alphabet_mapper is not None:
            return alphabet_mapper.get_base_form(dictionaryentry.title)
        else:
            return dictionaryentry.title

    @staticmethod
    def get_sorting_form(dictionaryentry):
        alphabet_mapper = dictionaryentry.site.alphabet_set.all()[0]
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
    page_size = 50

    def get_paginated_data(self, data):
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
