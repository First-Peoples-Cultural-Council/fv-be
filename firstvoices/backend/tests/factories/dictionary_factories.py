import factory
from django.utils.timezone import datetime
from factory.django import DjangoModelFactory

from backend.models import dictionary
from backend.tests.factories.access import SiteFactory, UserFactory
from backend.tests.factories.character_factories import CharacterFactory
from backend.tests.factories.dictionary_entry import DictionaryEntryFactory


class DictionaryModelFactory(DjangoModelFactory):
    dictionary_entry = factory.SubFactory(DictionaryEntryFactory)
    text = factory.Sequence(lambda n: "Sample text %03d" % n)


class DictionaryEntryLinkFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.DictionaryEntryLink

    from_dictionary_entry = factory.SubFactory(DictionaryEntryFactory)
    to_dictionary_entry = factory.SubFactory(DictionaryEntryFactory)


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.Category

    title = factory.Sequence(lambda n: "Category %03d" % n)
    site = factory.SubFactory(SiteFactory)
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)


class DictionaryEntryCategoryFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.DictionaryEntryCategory

    dictionary_entry = factory.SubFactory(DictionaryEntryFactory)
    category = factory.SubFactory(CategoryFactory)


class DictionaryEntryRelatedCharacterFactory(DjangoModelFactory):
    class Meta:
        model = dictionary.DictionaryEntryRelatedCharacter

    dictionary_entry = factory.SubFactory(DictionaryEntryFactory)
    character = factory.SubFactory(CharacterFactory)


class WordOfTheDayFactory(DjangoModelFactory):
    dictionary_entry = factory.SubFactory(DictionaryEntryFactory)
    date = datetime.today()

    class Meta:
        model = dictionary.WordOfTheDay
