from itertools import product

from backend.utils.character_utils import ArbSorter, CustomSorter, nfc


class TestCharacterUtils:
    chars = list("abcqwertyuiop")
    extra_chars = list("sfghjklzxvnm0987654321")
    non_char = "d"

    def test_arb_sorter_values(self):
        sorter = ArbSorter(order=self.chars)
        assert sorter.word_as_values("abc") == [0, 1, 2]
        assert sorter.word_as_values("d") == [10100]
        assert sorter.word_as_values("q") < sorter.word_as_values("p")

    def test_arb_sorter_ignorable(self):
        sorter = ArbSorter(order=self.chars, ignorable=list("/"))
        assert sorter.word_as_values("/") == []
        assert sorter.word_as_values("a/b/c") == [0, 1, 2]

    def test_custom_sorter_space(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.custom_sort_char(0) == " "

    def test_custom_sorter_base_chars(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.custom_sort_char(1) == "!"
        assert sorter.custom_sort_char(2) == "#"
        assert sorter.custom_sort_char(3) == "$"
        assert len(sorter.custom_order) == len(self.chars) + 1
        assert isinstance(sorter.custom_sort_char(len(self.chars)), str)
        assert sorter.custom_sort_char(len(self.chars) + 1) is None

    def test_custom_sorter_avoid_escape_chars(self):
        many_chars = self.chars + self.extra_chars
        sorter = CustomSorter(order=many_chars)
        assert '"' not in sorter.word_as_sort_string("".join(many_chars))
        assert "\\" not in sorter.word_as_sort_string("".join(many_chars))

    def test_custom_sorter_long_alphabet(self):
        double_chars = [a + b for (a, b) in product(self.chars, self.chars)]
        alph = self.chars + double_chars
        sorter = CustomSorter(order=alph)
        assert len(sorter.custom_order) == len(alph) + 1
        assert isinstance(sorter.custom_sort_char(150), str)

    def test_custom_sorter_oov_char(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.out_of_vocab_flag == "⚑"
        assert sorter.custom_sort_char(len(self.chars) + 1) is None
        assert sorter.custom_sort_char(10000 + ord("d")) == "⚑d"

    def test_custom_sort_string_basic(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.word_as_sort_string("abc") == "!#$"
        assert sorter.word_as_sort_string("ab c") == "!# $"
        assert sorter.word_as_sort_string("a") != sorter.word_as_sort_string("A")
        assert sorter.word_as_sort_string("d") == "⚑d"
        assert sorter.word_as_sort_string("abcd") == "!#$⚑d"
        assert sorter.word_as_sort_string("qwe") < sorter.word_as_sort_string("iop")

    def test_custom_sort_string_multichar(self):
        sorter = CustomSorter(order=["c", "ch", "a", "aa"])
        assert sorter.word_as_sort_string("ch") == sorter.custom_sort_char(2)
        assert sorter.word_as_sort_string("aa") == sorter.custom_sort_char(4)

    def test_custom_sort_string_ignorable(self):
        sorter = CustomSorter(order=["a", "aa", "c", "ch"], ignorable=list("/-"))
        assert sorter.word_as_sort_string("/-//") == ""
        assert sorter.word_as_sort_string("a/a") != sorter.custom_sort_char(2)
        assert sorter.word_as_sort_string("a/a") == sorter.custom_sort_char(1) * 2
        assert sorter.word_as_sort_string("c-h") == "$⚑h"

    def test_word_as_chars_basic(self):
        sorter = CustomSorter(order=self.chars)
        assert sorter.word_as_chars("abc") == ["a", "b", "c"]
        assert sorter.word_as_chars("ab c") == ["a", "b", " ", "c"]
        assert sorter.word_as_chars("abcd") == ["a", "b", "c", "d"]
        assert sorter.word_as_chars(" q we ") == [" ", "q", " ", "w", "e", " "]

    def test_word_as_chars_multichar(self):
        sorter = CustomSorter(order=["c", "ch", "a", "aa"])
        assert sorter.word_as_chars("ch") == ["ch"]
        assert sorter.word_as_chars("aa") == ["aa"]
        assert sorter.word_as_chars("cch") == ["c", "ch"]
        assert sorter.word_as_chars("aach") == ["aa", "ch"]

    def test_word_as_chars_special_characters(self):
        sorter = CustomSorter(order=["a", "aa", "c", "ch.", "h", "x-", "y", "-", "."])
        assert sorter.word_as_chars("x-y") == ["x-", "y"]
        assert sorter.word_as_chars("cch..") == ["c", "ch.", "."]
        assert sorter.word_as_chars("c-h") == ["c", "-", "h"]

    def test_nfc_normalization(self):
        expected_str = "ááááá"
        input_str = "ááááá"
        assert nfc(input_str) == expected_str
