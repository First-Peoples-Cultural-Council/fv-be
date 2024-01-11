import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from backend.models import Character
from backend.tests.factories import (
    CharacterFactory,
    CharacterVariantFactory,
    IgnoredCharacterFactory,
)
from backend.tests.test_models.test_media_models import RelatedVideoLinksValidationMixin
from backend.utils.character_utils import CustomSorter


class TestCharacterModel(RelatedVideoLinksValidationMixin):
    def create_instance_with_related_video_links(self, site, related_video_links):
        return CharacterFactory.create(
            site=site, related_video_links=related_video_links
        )

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
    def test_characters_onsave(self):
        """Character metadata is set on save"""
        char = CharacterFactory.create(title="a")
        char = Character.objects.get(id=char.id)
        char.title = char.title.upper()
        char.save()
        assert char.created != char.last_modified

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

    @pytest.mark.skip(reason="failing until fw-4438 is fixed")
    @pytest.mark.django_db
    def test_character_limit_addition(self):
        """Can't create more characters on a site than custom sort can handle"""
        limit = CustomSorter.max_alphabet_length

        char = CharacterFactory.create(title="c0")
        for n in range(1, limit):
            CharacterFactory.create(site=char.site, title="c" + str(n))

        assert Character.objects.filter(site=char.site).count() == limit

        with pytest.raises(ValidationError):
            CharacterFactory.create(site=char.site, title="c" + str(limit))

    @pytest.mark.skip(reason="failing until fw-4438 is fixed")
    @pytest.mark.django_db
    def test_character_limit_edit(self):
        """Can edit characters on a site that has the max amount"""
        limit = CustomSorter.max_alphabet_length

        char = CharacterFactory.create(title="c0")
        for n in range(1, limit):
            CharacterFactory.create(site=char.site, title="c" + str(n))

        assert Character.objects.filter(site=char.site).count() == limit

        char.title = "new title"
        char.save()  # should not raise a ValidationError

        assert char.title == "new title"
