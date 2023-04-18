import pytest
from django.db.utils import IntegrityError

from firstvoices.backend.tests.factories import (
    CharacterFactory,
    CharacterVariantFactory,
    IgnoredCharacterFactory,
)


class TestCharacterModel:
    @pytest.mark.django_db
    def test_characters_same_name(self):
        """Character can't be created with the same name as another"""
        char = CharacterFactory.create()
        with pytest.raises(IntegrityError):
            CharacterFactory.create(site=char.site, title=char.title)

    @pytest.mark.django_db
    def test_character_variant_same_name(self):
        """Variant can't be created with the same name as a character"""
        name = "a"
        char = CharacterFactory.create(title=name)
        with pytest.raises(IntegrityError):
            CharacterVariantFactory.create(
                site=char.site, title=name, base_character=char
            )

        name = "b"
        upper = "B"
        char = CharacterFactory.create(title=name)
        CharacterVariantFactory.create(base_character=char, title=upper)
        with pytest.raises(IntegrityError):
            CharacterFactory.create(site=char.site, title=upper)

    @pytest.mark.django_db
    def test_character_ignorable_same_name(self):
        """Ignorable can't be created with the same name as a character"""
        name = "a"
        char = CharacterFactory.create(title=name)
        with pytest.raises(IntegrityError):
            IgnoredCharacterFactory.create(site=char.site, title=name)

        ichar = IgnoredCharacterFactory.create()
        with pytest.raises(IntegrityError):
            CharacterFactory(site=ichar.site, title=ichar.title)

    @pytest.mark.django_db
    def test_variant_ignorable_same_name(self):
        """Ignorable can't be created with the same name as a character variant"""
        char = CharacterFactory.create()
        vchar = CharacterVariantFactory.create(base_character=char)
        with pytest.raises(IntegrityError):
            IgnoredCharacterFactory.create(site=char.site, title=vchar.title)

        char = CharacterFactory.create()
        ichar = IgnoredCharacterFactory.create(site=char.site)
        with pytest.raises(IntegrityError):
            CharacterVariantFactory.create(title=ichar.title, base_character=char)
