import logging
import re
import unicodedata


# From https://github.com/roedoejet/mothertongues/blob/master/mtd/processors/sorter.py
# with additions for ignorables and out-of-vocab chars (on branch: dev.sorter)
class ArbSorter:
    """Sort entries based on alphabet. Thanks to Lingweenie: https://lingweenie.org/conlang/sort.html

    Given a sequence of letters (arbitrary-length Unicode strings), convert each into a numerical code.
    Then, convert any string to be sorted into its numerical equivalent and sort on that.

    Examples:
        Here is an example of a sorter.

        >>> sorter = ArbSorter(['a', 'b', 'c'])
        >>> sorter.word_as_values('abc')
        [0, 1, 2]
        >>> sorter.values_as_word([0, 1, 2])
        'abc'

    Args:
        order (list[str]): The order to sort by.
    """

    def __init__(self, order: list[str], ignorable: list[str] | None = None):
        self.ignorable = [] if ignorable is None else ignorable
        split_order = [re.escape(x) for x in sorted(order, key=len, reverse=True)]
        self.splitter = re.compile(f'({"|".join(split_order)})', re.UNICODE)
        # Next, collect weights for the ordering.
        self.char_to_ord_lookup = {order[i]: i for i in range(len(order))}
        self.ord_to_char_lookup = {v: k for k, v in self.char_to_ord_lookup.items()}
        self.oov_start = 10000

    # Turns a word into a list of ints representing the new
    # lexicographic ordering.  Python, helpfully, allows one to
    # sort ordered collections of all types, including lists.
    def word_as_values(self, word: str) -> list[int]:
        """Turn word into values"""
        # ignore empty strings
        word = [x for x in self.splitter.split(word) if x]
        values = []
        for char in word:
            if char in self.ignorable:
                continue
            if char in self.char_to_ord_lookup:
                values.append(self.char_to_ord_lookup[char])
            else:
                # OOV (can be multiple OOVs strung together)
                for oov in char:
                    if oov in self.ignorable:
                        continue
                    oov_index = self.oov_start + ord(oov)
                    self.char_to_ord_lookup[oov] = oov_index
                    self.ord_to_char_lookup[oov_index] = oov
                    values.append(oov_index)
        return values

    def values_as_word(self, values: list[int]) -> str:
        """Turn values into word"""
        return "".join([self.ord_to_char_lookup[v] for v in values])

    def __call__(self, item_list, target, sort_key="sorting_form"):
        """Return sorted list based on item's (word's) sorting_form"""
        sorted_list = []
        for item in item_list:
            item[sort_key] = self.word_as_values(item[target])
            sorted_list.append(item)
        return sorted(sorted_list, key=lambda x: x[sort_key])


class CustomSorter(ArbSorter):
    """FV-specific custom sort tweaks.

    Adds space as first alphabet item. Defines a map from integer values
    to custom sort characters as a string. Adds a flag before out-of-vocab characters.

    Examples:
        >>> sorter = CustomSorter(['a', 'b', 'c'])
        >>> sorter.word_as_values('ab abcd')
        [1, 2, 0, 1, 2, 3, 10100]
        >>> sorter.word_as_sort_string('ab abcd')
        '!# !#$⚑d'
    """

    # Basic Latin plane (sans whitespace)
    basic_latin = range(32, 127)
    # Latin Extended planes A+B
    extended_latin = range(256, 592)
    # Remove double quote, backslash
    exclude_chars = [34, 92]

    max_alphabet_length = len(basic_latin) + len(extended_latin) - len(exclude_chars)

    space = " "
    out_of_vocab_flag = unicodedata.lookup("BLACK FLAG")

    logger = logging.getLogger(__name__)

    def __init__(self, order: list[str], ignorable: list[str] | None = None):
        order = [self.space] + order
        self._init_custom_order(len(order))

        super().__init__(order, ignorable)

    def _init_custom_order(self, alphabet_length: int) -> None:
        custom_char_range = [
            i
            for i in list(self.basic_latin) + list(self.extended_latin)
            if i not in self.exclude_chars
        ]
        if alphabet_length > len(custom_char_range):
            self.logger.warning(
                "Alphabet length ({}) exceeds possible custom order ({})".format(
                    alphabet_length, self.max_alphabet_length
                )
            )
        self.custom_order = [chr(i) for i in custom_char_range[0:alphabet_length]]

    def custom_sort_char(self, ord_value: int) -> str:
        """Converts a single character ord value to custom sort character equivalent"""
        if ord_value in range(len(self.custom_order)):
            return self.custom_order[ord_value]
        elif ord_value >= self.oov_start:
            return self.out_of_vocab_flag + chr(ord_value - self.oov_start)

    def word_as_sort_string(self, word):
        """Convert word into a string which unicode-sorts the same way list of int values does."""
        values = self.word_as_values(word)
        custom_chars = [self.custom_sort_char(i) for i in values]
        return "".join(custom_chars)

    def word_as_chars(self, word) -> list[str]:
        """Convert word into a list of characters for use in fv games."""
        values = self.word_as_values(word)
        chars = [self.ord_to_char_lookup[v] for v in values]
        return chars


def nfc(string: str) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", string))


def clean_input(string: str | None) -> str:
    if string is None:
        return ""
    return nfc(string.strip())
