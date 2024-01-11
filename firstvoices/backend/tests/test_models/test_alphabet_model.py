import pytest

from backend.models.characters import AppJson
from backend.tests.factories import (
    AlphabetFactory,
    CharacterFactory,
    CharacterVariantFactory,
    IgnoredCharacterFactory,
)
from backend.utils.character_utils import clean_input


class TestAlphabetModel:
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
        assert alphabet.clean_confusables("test") == "test"
        assert alphabet.clean_confusables(r"^^a") == "AAa"
        assert alphabet.clean_confusables(r"test.") == "testo"
        assert alphabet.clean_confusables(r"testing.") == "testing"
        assert alphabet.clean_confusables(r"\d\d") == "DD"

    @pytest.mark.django_db
    def test_get_character_list(self, alphabet):
        """Get list of characters in text, split with current alphabet and MTD splitter, base and variant characters"""
        aa = CharacterFactory(site=alphabet.site, title="aa")
        ch = CharacterFactory(site=alphabet.site, title="ch")
        CharacterFactory(site=alphabet.site, title="c")
        CharacterFactory(site=alphabet.site, title="d")
        e = CharacterFactory(site=alphabet.site, title="e")
        CharacterVariantFactory(site=alphabet.site, title="AA", base_character=aa)
        CharacterVariantFactory(site=alphabet.site, title="Ch", base_character=ch)
        CharacterVariantFactory(site=alphabet.site, title="E", base_character=e)

        s = "deaaChcchdAA CH"
        assert alphabet.get_character_list(s) == [
            "d",
            "e",
            "aa",
            "Ch",
            "c",
            "ch",
            "d",
            "AA",
            " ",
            "C",
            "H",
        ]

    @pytest.mark.django_db
    def test_get_base_form(self, alphabet):
        """Get base form of text"""
        x = CharacterFactory(site=alphabet.site, title="x")
        y = CharacterFactory(site=alphabet.site, title="y")
        CharacterVariantFactory(site=alphabet.site, title="X", base_character=x)
        CharacterVariantFactory(site=alphabet.site, title="Y", base_character=y)

        s = "XxYy"
        assert alphabet.get_base_form(s) == "xxyy"

    @pytest.mark.django_db
    def test_get_base_form_with_special_characters(self, alphabet):
        """Get base form of text with confusables applied"""
        CharacterFactory(site=alphabet.site, title="-")
        CharacterFactory(site=alphabet.site, title=".")
        CharacterFactory(site=alphabet.site, title="&")
        a = CharacterFactory(site=alphabet.site, title="a")
        b = CharacterFactory(site=alphabet.site, title="b")
        c = CharacterFactory(site=alphabet.site, title="c")
        CharacterVariantFactory(site=alphabet.site, title="A", base_character=a)
        CharacterVariantFactory(site=alphabet.site, title="B", base_character=b)
        CharacterVariantFactory(site=alphabet.site, title="C", base_character=c)

        s = "ABC-.-&"
        base = alphabet.get_base_form(s)
        assert base == "abc-.-&"

    @pytest.mark.django_db
    def test_cleaned_form_is_normalized(self):
        """Clean confusables can't produce a non-normalized string"""
        alphabet = AlphabetFactory.create(
            input_to_canonical_map=[{"in": "ẕ", "out": "z̲"}],
        )
        CharacterFactory(site=alphabet.site, title="z̲")

        s = "ẕ́"
        new_form = alphabet.clean_confusables(s)
        assert new_form == clean_input(new_form)
        order = alphabet.get_custom_order(new_form)
        # custom order is successful and reflects nfc ordering issue
        assert order == "⚑ź⚑̲"
