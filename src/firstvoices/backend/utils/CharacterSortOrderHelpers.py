import json
import re
import unicodedata

from firstvoices.backend.models.characters import (
    Character,
    CharacterVariant,
    IgnoredCharacter,
)


# From MTD processors
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
                # OOV (can be multiple OOVs strung together) # TODO: what does this mean?
                for oov in char:
                    if oov in self.ignorable:  # TODO: is this required
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
    # Remove double quote
    exclude_chars = [34]

    space = " "
    out_of_vocab_flag = unicodedata.lookup("BLACK FLAG")

    def __init__(self, order: list[str], ignorable: list[str] | None = None):
        order.insert(0, self.space)
        self._init_custom_order(len(order))

        super().__init__(order, ignorable)

    def _init_custom_order(self, alphabet_length: int) -> None:
        custom_char_range = [i for i in self.basic_latin if i not in self.exclude_chars]

        if alphabet_length > len(custom_char_range):
            supplementary_chars = [
                i for i in self.extended_latin if i not in self.exclude_chars
            ]
            custom_char_range += supplementary_chars

        self.custom_order = [chr(i) for i in custom_char_range[0:alphabet_length]]
        # print("Custom order:", self.custom_order, f"({len(self.custom_order)} chars)")
        # Custom order: [' ', '!', '#', '$', '%'] (5 chars)

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


# TODO: Find a better place to put  the NFC function
def nfc(string: str) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", string))


class SiteG2PMappingGenerator:
    """Generates the appropriate site mappings for a given site"""

    @staticmethod
    def generate_preprocess_map(
        base_characters: list[Character],
        variants: list[CharacterVariant],
        confusable_chars: dict[str, list[str]],
        ignored_chars: list[IgnoredCharacter],
        site_config_yaml: str,
    ):
        """Generates the confusable to canonical g2p mapping."""

        base_character_info = [
            {"title": char.title, "order": char.sort_order} for char in base_characters
        ]
        variant_character_map = {}

        variant_character_map.update(
            {variant.title: variant.base_character.title} for variant in variants
        )

        variant_character_map.update(
            {char["title"]: char["title"] for char in base_character_info}
        )

        ignorables = [char.title for char in ignored_chars]
        confusables_source = confusable_chars

        # get a list of confusables mapped to their parent variant + some validation
        confusables_map = {}
        duplicates = []
        for variant, confusables in confusables_source.items():
            for confusable in {nfc(c) for c in confusables}:
                if (confusable in variant_character_map) or (confusable in ignorables):
                    print("Skipping confusable {} -- same as a canonical character")
                elif confusable in confusables_map:
                    duplicates.append(confusable)
                else:
                    confusables_map[confusable] = variant
        if duplicates:
            for duplicate_confusable in set(duplicates):
                print("Removing confusable {} -- duplicated")
                del confusables_map[confusable]

        preprocessor_map = json.dumps(
            [
                {"in": confusable, "out": canonical}
                for confusable, canonical in confusables_map.items()
            ],
            ensure_ascii=False,
        )

        return preprocessor_map

    @staticmethod
    def generate_presort_map(
        base_chars: list[Character],
        variants: list[CharacterVariant],
    ):
        """Generates the canonical to base g2p mapping csv file."""

        base_character_info = [
            {"title": char.title, "order": char.sort_order} for char in base_chars
        ]
        variant_character_map = [
            {variant.title: variant.base_character.title} for variant in variants
        ]

        variant_character_map.update(
            {char["title"]: char["title"] for char in base_character_info}
        )

        presorter_map = json.dumps(
            [
                {"in": variant, "out": base}
                for variant, base in variant_character_map.items()
            ],
            ensure_ascii=False,
        )

        return presorter_map
