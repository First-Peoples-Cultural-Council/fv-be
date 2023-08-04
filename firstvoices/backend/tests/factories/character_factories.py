import factory
from factory.django import DjangoModelFactory

from backend.models import Alphabet, Character, CharacterVariant, IgnoredCharacter
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.access import SiteFactory, UserFactory


class CharacterFactory(RelatedMediaBaseFactory):
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Character

    title = factory.Sequence(lambda n: "chr" + chr(n + 64))  # begin with A
    sort_order = factory.Sequence(int)


class CharacterVariantFactory(DjangoModelFactory):
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = CharacterVariant

    base_character = factory.SubFactory(CharacterFactory)
    title = factory.Sequence(lambda n: "varchr" + chr(n + 64))  # begin with A


class IgnoredCharacterFactory(DjangoModelFactory):
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = IgnoredCharacter

    title = factory.Sequence(lambda n: "%03d" % n)


class AlphabetFactory(DjangoModelFactory):
    created_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Alphabet
