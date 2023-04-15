import pytest
from django.core.management import call_command
from django.db.utils import IntegrityError

from firstvoices.backend.models.characters import AppJson
from firstvoices.backend.tests.factories import (
    AlphabetFactory,
    CharacterFactory,
    CharacterVariantFactory,
    IgnoredCharacterFactory,
)


class TestAlphabetModel:
    @pytest.fixture(scope="session")
    def g2p_db_setup(self, django_db_setup, django_db_blocker):
        with django_db_blocker.unblock():
            call_command("loaddata", "default_g2p_config.json")

    @pytest.fixture
    def alphabet(self):
        return AlphabetFactory.create()

    @pytest.mark.django_db
    def test_load_config_fixture(self):
        """Default g2p config settings loaded from fixture"""
        settings = AppJson.objects.get(key="default_g2p_config").json
        assert settings is not None
        assert "preprocess_config" in settings

    @pytest.mark.django_db
    def test_sort_no_characters(self, alphabet):
        """When no characters are defined, alphabet uses basic sort"""
        assert alphabet.get_custom_order("a") < alphabet.get_custom_order("b")

    @pytest.mark.django_db
    def test_sort_characters(self, alphabet):
        """When characters are defined, alphabet uses custom sort"""
        CharacterFactory(site=alphabet.site, title="b", sort_order=1)
        CharacterFactory(site=alphabet.site, title="a", sort_order=2)
        assert alphabet.get_custom_order("a") > alphabet.get_custom_order("b")

    @pytest.mark.django_db
    def test_sort_variant_insensitive(self, alphabet):
        """When variants are defined, their sort equals base character sort"""
        char_a = CharacterFactory(site=alphabet.site, title="a")
        CharacterVariantFactory(site=alphabet.site, title="A", base_character=char_a)
        CharacterVariantFactory(site=alphabet.site, title="ᐱ", base_character=char_a)
        assert alphabet.get_custom_order("a") == alphabet.get_custom_order("A")
        assert alphabet.get_custom_order("a") == alphabet.get_custom_order("ᐱ")
        assert alphabet.get_custom_order("aAᐱ*") == alphabet.get_custom_order("ᐱaA*")

    @pytest.mark.django_db
    def test_sort_skip_ignorables(self, alphabet):
        """When ignorable characters are defined, they are ignored from sort"""
        CharacterFactory(site=alphabet.site, title="a")
        IgnoredCharacterFactory(site=alphabet.site, title="x")
        assert alphabet.get_custom_order("x") == alphabet.get_custom_order("")
        assert alphabet.get_custom_order("ax") == alphabet.get_custom_order("a")
        assert alphabet.get_custom_order("xa") == alphabet.get_custom_order("a")
        assert alphabet.get_custom_order("xaxaxax") == alphabet.get_custom_order("aaa")

    @pytest.mark.django_db
    def test_sort_regex_insensitive(self, alphabet):
        """Regex characters are escaped in variant-character transductions"""
        char_a = CharacterFactory(site=alphabet.site, title="A")
        char_o = CharacterFactory(site=alphabet.site, title="o")
        char_n = CharacterFactory(site=alphabet.site, title="\\n")
        CharacterVariantFactory(title="^", base_character=char_a)
        CharacterVariantFactory(title=".", base_character=char_o)
        CharacterVariantFactory(title="n", base_character=char_n)
        assert alphabet.get_custom_order("^") == alphabet.get_custom_order("A")
        assert alphabet.get_custom_order("..") == alphabet.get_custom_order("oo")
        assert alphabet.get_custom_order("..") != alphabet.get_custom_order("12")
        assert alphabet.get_custom_order("\\n\\n") == alphabet.get_custom_order("nn")
        assert alphabet.get_custom_order("\n\n") != alphabet.get_custom_order("nn")

    @pytest.mark.django_db
    def test_clean_confusables_basic(self):
        """Apply confusable transducer as defined in alphabet"""
        alphabet = AlphabetFactory.create(
            input_to_canonical_map=[
                {"in": "á", "out": "a"},
                {"in": "ᐱ", "out": "A"},
                {"in": "_b", "out": "b"},
                {"in": "č", "out": "cv"},
            ],
        )
        assert alphabet.clean_confusables("X") == "X"
        assert alphabet.clean_confusables("á") == "a"
        assert alphabet.clean_confusables("_b") == "b"
        assert alphabet.clean_confusables("č") == "cv"
        assert alphabet.clean_confusables("áx ᐱᐱᐱ") == "ax AAA"
        assert alphabet.clean_confusables("aᐱᐱx _bč") == "aAAx bcv"
        IgnoredCharacterFactory(site=alphabet.site, title="/")
        assert alphabet.clean_confusables("ᐱ/_/b/č") == "A/_/b/cv"

    @pytest.mark.django_db
    def test_clean_confusables_no_feeding(self):
        """Default confusables transducer does not allow multi-rule application"""
        alphabet = AlphabetFactory.create(
            input_to_canonical_map=[
                {"in": "AA", "out": "A"},
                {"in": "A", "out": "a"},
                {"in": "č", "out": "c"},
                {"in": "čh", "out": "čh"},
            ],
        )
        assert alphabet.clean_confusables("A") == "a"
        assert alphabet.clean_confusables("AA") == "A"
        assert alphabet.clean_confusables("AAA") == "Aa"
        assert alphabet.clean_confusables("č") == "c"
        assert alphabet.clean_confusables("čh") == "čh"
        IgnoredCharacterFactory(site=alphabet.site, title="/")
        assert alphabet.clean_confusables("A/A") == "a/a"

    @pytest.mark.skip("g2p regex escape seems to ignore the mapping with escaped char?")
    @pytest.mark.django_db
    def test_clean_confusables_regex_escape(self):
        """Default confusables transducer ignores regex rules"""
        alphabet = AlphabetFactory.create(
            input_to_canonical_map=[
                {"in": r"^", "out": "A"},
                {"in": r".", "out": "o"},
                {"in": r"ng.", "out": "ng"},
                {"in": r"\d", "out": "D"},
            ],
        )
        assert len(alphabet.input_to_canonical_map) == 4
        assert alphabet.clean_confusables("test") == "test"
        assert alphabet.clean_confusables(r"^^a") == "AAa"
        assert alphabet.clean_confusables(r"test.") == "testo"
        assert alphabet.clean_confusables(r"testing.") == "testing"
        assert alphabet.clean_confusables(r"\d\d") == "DD"


class TestCharacterModel:
    @pytest.mark.django_db
    def test_characters_same_name(self):
        """Character can't be created with the same name as another"""
        char = CharacterFactory.create()
        with pytest.raises(IntegrityError):
            CharacterFactory.create(site=char.site, title=char.title)

    @pytest.mark.skip("cross model uniqueness")
    @pytest.mark.django_db
    def test_character_variant_same_name(self):
        """Variant can't be created with the same name as a character"""
        char = CharacterFactory.create()
        with pytest.raises(IntegrityError):
            CharacterVariantFactory.create(site=char.site, title=char.title)

        char = CharacterFactory.create()
        var_char = CharacterVariantFactory(base_character=char)
        with pytest.raises(IntegrityError):
            CharacterFactory.create(site=char.site, title=var_char.title)

    @pytest.mark.skip("cross model uniqueness")
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

    @pytest.mark.skip("cross model uniqueness")
    @pytest.mark.django_db
    def test_variant_ignorable_same_name(self):
        """Ignorable can't be created with the same name as a character variant"""
        char = CharacterFactory.create()
        with pytest.raises(IntegrityError):
            IgnoredCharacterFactory.create(site=char.site, title=char.title)

        char = CharacterFactory.create()
        ichar = IgnoredCharacterFactory.create(site=char.site)
        with pytest.raises(IntegrityError):
            CharacterVariantFactory.create(title=ichar.title, base_character=char)

    # TODO: can't create over 429 characters - custom sorter max
