from django.db.models import Q
from rest_framework import serializers

from backend.models import Category, PartOfSpeech, Site
from backend.models.constants import Visibility
from backend.models.dictionary import TypeOfDictionaryEntry


class CategoryCountSerializer(serializers.Serializer):
    title = serializers.SerializerMethodField()
    words = serializers.SerializerMethodField()
    phrases = serializers.SerializerMethodField()

    def get_title(self, dictionary_entries):
        id = self.context["category_id"]
        return Category.objects.get(pk=id).title

    def get_words(self, dictionary_entries):
        return self.get_count_by_type(dictionary_entries, TypeOfDictionaryEntry.WORD)

    def get_phrases(self, dictionary_entries):
        return self.get_count_by_type(dictionary_entries, TypeOfDictionaryEntry.PHRASE)

    def get_count_by_type(self, dictionary_entries, entry_type):
        category = self.context["category_id"]
        category_ids = [
            c
            for c in Category.objects.filter(parent=category).values_list(
                "id", flat=True
            )
        ]
        category_ids.append(category)
        return (
            dictionary_entries.filter(
                dictionaryentrycategory_set__category__in=category_ids
            )
            .distinct()
            .count()
        )


class PartOfSpeechCountSerializer(serializers.Serializer):
    title = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    def get_title(self, dictionary_entries):
        pos_id = self.context["part_of_speech"]
        return PartOfSpeech.objects.get(pk=pos_id).title

    def get_count(self, dictionary_entries):
        pos_id = self.context["part_of_speech"]
        return dictionary_entries.filter(part_of_speech=pos_id).distinct().count()


class ContentProblemsSerializer(serializers.Serializer):
    team_only = serializers.SerializerMethodField()
    missing_audio = serializers.SerializerMethodField()
    missing_image = serializers.SerializerMethodField()

    def get_team_only(self, dictionary_entries):
        return self.count_by_visibility(dictionary_entries, Visibility.TEAM)

    def count_by_visibility(self, dictionary_entries, visibility):
        return dictionary_entries.filter(visibility=visibility).count()

    def get_missing_audio(self, dictionary_entries):
        return dictionary_entries.filter(related_audio__isnull=True).count()

    def get_missing_image(self, dictionary_entries):
        return dictionary_entries.filter(related_images__isnull=True).count()


class DictionaryProblemsSerializer(ContentProblemsSerializer):
    missing_translation = serializers.SerializerMethodField()
    missing_category = serializers.SerializerMethodField()

    def get_missing_translation(self, dictionary_entries):
        return dictionary_entries.filter(translations__len=0).count()

    def get_missing_category(self, dictionary_entries):
        return dictionary_entries.filter(
            dictionaryentrycategory_set__isnull=True
        ).count()


class ContentCountSerializer(serializers.Serializer):
    published = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()

    problem_serializer_class = ContentProblemsSerializer

    def get_published(self, queryset):
        return queryset.filter(visibility__gte=Visibility.MEMBERS).count()

    def get_notes(self, queryset):
        return self.problem_serializer_class(
            queryset, context=self.context, read_only=True
        ).data


class DictionaryCountSerializer(ContentCountSerializer):
    problem_serializer_class = DictionaryProblemsSerializer
    full_entries = serializers.SerializerMethodField()

    def get_full_entries(self, dictionary_entries):
        full_entries = (
            dictionary_entries.filter(translations__len__gte=1)
            .filter(related_audio__isnull=False)
            .filter(visibility__gte=Visibility.MEMBERS)
            .distinct()
        )
        return DictionaryCountDetailsSerializer(full_entries, context=self.context).data


class DictionaryCountDetailsSerializer(serializers.Serializer):
    words = serializers.SerializerMethodField()
    phrases = serializers.SerializerMethodField()
    words_with_example_phrases = serializers.SerializerMethodField()

    by_category = serializers.SerializerMethodField()
    by_key_part_of_speech = serializers.SerializerMethodField()

    def get_words(self, dictionary_entries):
        return self.get_count_by_type(dictionary_entries, TypeOfDictionaryEntry.WORD)

    def get_phrases(self, dictionary_entries):
        return self.get_count_by_type(dictionary_entries, TypeOfDictionaryEntry.PHRASE)

    def get_count_by_type(self, dictionary_entries, entry_type):
        return dictionary_entries.filter(type=entry_type).count()

    def get_words_with_example_phrases(self, dictionary_entries):
        return (
            dictionary_entries.filter(type=TypeOfDictionaryEntry.WORD)
            .filter(related_dictionary_entries__type=TypeOfDictionaryEntry.PHRASE)
            .count()
        )

    def get_by_category(self, dictionary_entries):
        if dictionary_entries.count() > 0:
            site = dictionary_entries.first().site
            top_level_categories = (
                Category.objects.filter(site=site).filter(parent=None).distinct()
            )

            return [
                CategoryCountSerializer(
                    dictionary_entries, context={"category_id": c.id}
                ).data
                for c in top_level_categories
            ]

    def get_by_key_part_of_speech(self, dictionary_entries):
        if dictionary_entries.count() > 0:
            site = dictionary_entries.first().site
            basic_pos = PartOfSpeech.objects.filter(
                Q(title="Verb")
                | Q(title="Noun")
                | Q(title="Pronoun")
                | Q(title="Adjective")
                | Q(title="Adverb")
                | Q(title="Conjunction")
                | Q(title="Interjection")
                | Q(title="Question Word")
                | Q(title="Preposition")
                | Q(title="Postposition")
            )

            return [
                PartOfSpeechCountSerializer(
                    dictionary_entries,
                    context={"site_id": site.id, "part_of_speech": p.pk},
                ).data
                for p in basic_pos
            ]


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializes statistics about the data on a Site, for use in internal reporting.
    """

    slug = serializers.CharField(read_only=True)
    language = serializers.StringRelatedField(read_only=True)
    dictionary_entries = DictionaryCountSerializer(
        source="dictionaryentry_set", read_only=True
    )
    songs = ContentCountSerializer(source="song_set", read_only=True)
    stories = ContentCountSerializer(source="story_set", read_only=True)

    class Meta:
        model = Site
        fields = [
            "slug",
            "language",
            "dictionary_entries",
            "songs",
            "stories",
        ]
