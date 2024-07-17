from rest_framework import serializers

from backend.models import Category
from backend.models.dictionary import DictionaryEntry, TypeOfDictionaryEntry
from backend.models.media import Audio, Image, Video


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


class MediaDataSerializer(serializers.ModelSerializer):
    filename = serializers.FileField(source="original.content")

    class Meta:
        fields = ("filename",)


class AudioDataSerializer(MediaDataSerializer):
    description = serializers.SerializerMethodField()

    @staticmethod
    def get_description(audio):
        speakers = audio.speakers.all()
        name = speakers[0].name if speakers.count() > 0 else None
        return name

    class Meta:
        model = Audio
        fields = MediaDataSerializer.Meta.fields + ("description",)


class VideoDataSerializer(MediaDataSerializer):
    description = serializers.SerializerMethodField()

    @staticmethod
    def get_description(video):
        return (
            video.description
            if video.description and len(video.description) > 0
            else None
        )

    class Meta:
        model = Video
        fields = MediaDataSerializer.Meta.fields + ("description",)


class ImageDataSerializer(MediaDataSerializer):
    class Meta:
        model = Image
        fields = MediaDataSerializer.Meta.fields


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
    sorting_form = serializers.SerializerMethodField()

    @staticmethod
    def get_source(dictionaryentry):
        return dict_entry_type_mtd_conversion(dictionaryentry.type)

    @staticmethod
    def get_definition(dictionary_entry):
        if len(dictionary_entry.translations) > 0:
            return dictionary_entry.translations[0]
        else:
            return None

    @staticmethod
    def get_audio(dictionaryentry):
        return AudioDataSerializer(dictionaryentry.related_audio, many=True).data

    @staticmethod
    def get_video(dictionaryentry):
        return VideoDataSerializer(dictionaryentry.related_videos, many=True).data

    @staticmethod
    def get_img(dictionaryentry):
        # NOTE: MTD currently only allows one image. As a heuristic, I'm selecting the first one.
        return ImageDataSerializer(dictionaryentry.related_images.first()).data[
            "filename"
        ]

    @staticmethod
    def get_theme(dictionaryentry):
        # NOTE: MTD currently only allows one theme and one secondary theme
        #       As a heuristic, I'm selecting the first theme with both a main
        #       and secondary theme. If that doesn't exist, I just select the first theme.
        first_theme = (
            dictionaryentry.categories.filter(parent__isnull=False).first()
            or dictionaryentry.categories.first()
        )
        # Return None if no theme available
        if first_theme is None:
            return None
        # The theme is equal to the parent theme if it exists
        if first_theme.parent is not None:
            return first_theme.parent.title
        # Otherwise just return the theme title
        return first_theme.title

    @staticmethod
    def get_sort_form(dictionaryentry):
        alphabet_mapper = dictionaryentry.site.alphabet_set.all()[0]
        if alphabet_mapper is not None:
            return alphabet_mapper.get_base_form(dictionaryentry.title)
        else:
            return dictionaryentry.title

    @staticmethod
    def get_secondary_theme(dictionaryentry):
        # NOTE: MTD currently only allows one theme and one secondary theme
        #       As a heuristic, I'm selecting the first theme with both a main
        #       and secondary theme. If that doesn't exist, I just select the first theme.
        first_theme = (
            dictionaryentry.categories.filter(parent__isnull=False).first()
            or dictionaryentry.categories.first()
        )
        return (
            first_theme.title
            if first_theme and first_theme.parent is not None
            else None
        )

    @staticmethod
    def get_optional(dictionary_entry):
        optional_information = {}
        if len(dictionary_entry.acknowledgements):
            optional_information["Reference"] = dictionary_entry.acknowledgements[0]
        if len(dictionary_entry.notes):
            optional_information["Note"] = dictionary_entry.notes[0]
        if dictionary_entry.part_of_speech is not None:
            optional_information[
                "Part of Speech"
            ] = dictionary_entry.part_of_speech.title
        return optional_information

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
            "sorting_form",
        )
