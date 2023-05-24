import factory
from factory.django import DjangoModelFactory

from backend.models import Alphabet, Character, CharacterVariant, IgnoredCharacter
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.access import SiteFactory


class CharacterFactory(RelatedMediaBaseFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Character

    title = factory.Sequence(lambda n: "chr" + chr(n + 64))  # begin with A
    sort_order = factory.Sequence(int)


class CharacterVariantFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = CharacterVariant

    base_character = factory.SubFactory(CharacterFactory)
    title = factory.Sequence(lambda n: "varchr" + chr(n + 64))  # begin with A


class IgnoredCharacterFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = IgnoredCharacter

    title = factory.Sequence(lambda n: "%03d" % n)


class AlphabetFactory(DjangoModelFactory):
    site = factory.SubFactory(SiteFactory)

    class Meta:
        model = Alphabet
