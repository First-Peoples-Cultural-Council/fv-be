import factory

from backend.models import Alphabet, Character, CharacterVariant, IgnoredCharacter
from backend.tests.factories import RelatedMediaBaseFactory
from backend.tests.factories.base_factories import SiteContentFactory


class CharacterFactory(RelatedMediaBaseFactory, SiteContentFactory):
    class Meta:
        model = Character

    title = factory.Sequence(lambda n: "chr" + chr(n + 64))  # begin with A
    sort_order = factory.Sequence(int)


class CharacterVariantFactory(SiteContentFactory):
    class Meta:
        model = CharacterVariant

    base_character = factory.SubFactory(CharacterFactory)
    title = factory.Sequence(lambda n: "varchr" + chr(n + 64))  # begin with A


class IgnoredCharacterFactory(SiteContentFactory):
    class Meta:
        model = IgnoredCharacter

    title = factory.Sequence(lambda n: "%03d" % n)


class AlphabetFactory(SiteContentFactory):
    class Meta:
        model = Alphabet
