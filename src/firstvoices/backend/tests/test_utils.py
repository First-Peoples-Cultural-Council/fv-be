from itertools import product

from ..utils.character_utils import ArbSorter, CustomSorter


class TestCharacterUtils:
    def test_arb_sorter_values(self):
        sorter = ArbSorter(order=list("abc"))
        assert sorter.word_as_values("abc") == [0, 1, 2]
        assert sorter.word_as_values("d") == [10100]

    def test_arb_sorter_ignorable(self):
        sorter = ArbSorter(order=list("abc"), ignorable=list("/"))
        assert sorter.word_as_values("/") == []
        assert sorter.word_as_values("a/b/c") == [0, 1, 2]

    def test_custom_sorter_space(self):
        sorter = CustomSorter(order=list("abc"))
        assert sorter.custom_sort_char(0) == " "

    def test_custom_sorter_base_chars(self):
        chars = list("abc")
        sorter = CustomSorter(order=chars)

        assert isinstance(sorter.custom_sort_char(0), str)
        assert isinstance(sorter.custom_sort_char(len(chars)), str)
        # skip double quote in the ascii plane for readability
        assert sorter.custom_sort_char(2) != '"'

        expected = "!#$"
        for index, char in enumerate(expected):
            assert sorter.custom_sort_char(index + 1) == char

        assert len(sorter.custom_order) == len(chars) + 1

    def test_custom_sorter_long_alphabet(self):
        singles = "qwertyuiopasdfghjkl"
        doubles = [a + b for (a, b) in product(list(singles), list(singles))]
        sorter = CustomSorter(order=doubles)
        assert isinstance(sorter.custom_sort_char(100), str)
        assert isinstance(sorter.custom_sort_char(len(doubles)), str)
        assert len(sorter.custom_order) == len(doubles) + 1

    def test_custom_sorter_oov_char(self):
        chars = list("abc")
        sorter = CustomSorter(order=chars)
        assert sorter.out_of_vocab_flag == "⚑"
        assert sorter.custom_sort_char(len(chars) + 1) is None
        assert sorter.custom_sort_char(10000 + ord("d")) == "⚑d"

    def test_custom_sort_string_basic(self):
        sorter = CustomSorter(order=list("abcABC"))
        assert sorter.word_as_sort_string("abc") == "!#$"
        assert sorter.word_as_sort_string("ab c") == "!# $"
        assert sorter.word_as_sort_string("a") != sorter.word_as_sort_string("A")
        assert sorter.word_as_sort_string("d") == "⚑d"
        assert sorter.word_as_sort_string("abcd") == "!#$⚑d"

    def test_custom_sort_string_multichar(self):
        sorter = CustomSorter(order=["a", "aa", "c", "ch"])
        assert sorter.word_as_sort_string("aa") == sorter.custom_sort_char(2)
        assert sorter.word_as_sort_string("ch") == sorter.custom_sort_char(4)

    def test_custom_sort_string_ignorable(self):
        sorter = CustomSorter(order=["a", "aa", "c", "ch"], ignorable=list("/-"))
        assert sorter.word_as_sort_string("a/a") != sorter.custom_sort_char(2)
        assert sorter.word_as_sort_string("a/a") == sorter.custom_sort_char(1) * 2
        assert sorter.word_as_sort_string("c-h") == "$⚑h"
