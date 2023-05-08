import factory
from django.utils.timezone import datetime
from factory.django import DjangoModelFactory

from backend.models import PartOfSpeech, dictionary
from backend.tests import factories


class DictionaryModelFactory(DjangoModelFactory):
    dictionary_entry = factory.SubFactory(factories.DictionaryEntryFactory)


class AcknowledgementFactory(DictionaryModelFactory):
    class Meta:
        model = dictionary.Acknowledgement


class AlternateSpellingFactory(DictionaryModelFactory):
    class Meta:
        model = dictionary.AlternateSpelling


class NoteFactory(DictionaryModelFactory):
    class Meta:
        model = dictionary.Note


class PronunciationFactory(DictionaryModelFactory):
    class Meta:
        model = dictionary.Pronunciation


class TranslationFactory(DictionaryModelFactory):
    class Meta:
        model = dictionary.Translation


class DictionaryEntryLinkFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.DictionaryEntryLink

    from_dictionary_entry = factory.SubFactory(factories.DictionaryEntryFactory)
    to_dictionary_entry = factory.SubFactory(factories.DictionaryEntryFactory)


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.Category

    title = factory.Sequence(lambda n: "Category %03d" % n)
    site = factory.SubFactory(factories.SiteFactory)
    created_by = factory.SubFactory(factories.UserFactory)
    last_modified_by = factory.SubFactory(factories.UserFactory)


class DictionaryEntryCategoryFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.DictionaryEntryCategory

    dictionary_entry = factory.SubFactory(factories.DictionaryEntryFactory)
    category = factory.SubFactory(CategoryFactory)


class DictionaryEntryRelatedCharacterFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.DictionaryEntryRelatedCharacter

    dictionary_entry = factory.SubFactory(factories.DictionaryEntryFactory)
    character = factory.SubFactory(factories.CharacterFactory)


class PartOfSpeechFactory(DjangoModelFactory):
    class Meta:
        model = PartOfSpeech

    title = factory.Sequence(lambda n: "Part of Speech %03d" % n)
    created_by = factory.SubFactory(factories.UserFactory)
    last_modified_by = factory.SubFactory(factories.UserFactory)


class WordOfTheDayFactory(DjangoModelFactory):
    dictionary_entry = factory.SubFactory(factories.DictionaryEntryFactory)
    date = datetime.today()

    class Meta:
        model = dictionary.WordOfTheDay
