import re
import unicodedata
from typing import Optional
import json
import os
import yaml
import g2p


# From MTD processors
class ArbSorter(object):
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

    def __init__(self, order: list[str], ignorable: Optional[list[str]] = None):
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

    def __init__(self, order: list[str], ignorable: Optional[list[str]] = None):
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


def nfc(string: str) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", string))


# load some sample data

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "sort_sample.json")) as f:
    sample_data = json.load(f)

site = sample_data["sample_site"]
site_name = "FV {name}".format(name=site["title"])
site_code = "fv-{slug}".format(slug=site["slug"])

base_chars = sample_data["chars"]
variant_chars_map = sample_data["vars"]
# validate that there are no duplicate variants -- should be done at DB level
ignorables = sample_data["ignorables"]


# create input-canonical mapper for a site with migrated confusables list
# TODO: alternative - load map contents from db once they exist
# TODO: be able to generate new mapper from master confusables list for a new site

variant_chars_map.update({char["name"]: char["name"] for char in base_chars})

confusables_source = sample_data["confusables"]

# get a list of confusables mapped to their parent variant + some validation
confusables_map = {}
duplicates = []
for variant, confusables in confusables_source.items():
    for confusable in set([nfc(c) for c in confusables]):
        if (confusable in variant_chars_map) or (confusable in ignorables):
            print("Skipping confusable {} -- same as a canonical character")
        elif confusable in confusables_map:
            duplicates.append(confusable)
        else:
            confusables_map[confusable] = variant
if duplicates:
    for duplicate_confusable in set(duplicates):
        print("Removing confusable {} -- duplicated")
        del confusables_map[confusable]


# save input-canonical and canonical-base mappers as text

preprocessor_map = json.dumps(
    [
        {"in": confusable, "out": canonical}
        for confusable, canonical in confusables_map.items()
    ],
    ensure_ascii=False,
)

presorter_map = json.dumps(
    [{"in": variant, "out": base} for variant, base in variant_chars_map.items()],
    ensure_ascii=False,
)


# generate mapper configuration

with open(os.path.join(here, "default_config.yaml")) as f:
    default_config = f.read()

site_config = default_config.format(language=site_name, code=site_code)
site_config = yaml.safe_load(site_config)

# identify mappers for both transduction steps
input_name = site_code + "-input"
canonical_name = site_code
output_name = site_code + "-base"

for mapping in site_config["mappings"]:
    if mapping["in_lang"] == input_name and mapping["out_lang"] == canonical_name:
        preprocess_settings = mapping
    elif mapping["in_lang"] == canonical_name and mapping["out_lang"] == output_name:
        presort_settings = mapping


# this concludes setup.
# further steps assume we have saved or stored our alphabet and mappers.


# create transducers

preprocessor = g2p.Transducer(
    g2p.Mapping(**preprocess_settings, mapping=json.loads(preprocessor_map))
)

presorter = g2p.Transducer(
    g2p.Mapping(**presort_settings, mapping=json.loads(presorter_map))
)


# load alphabet into custom sorter for generating sort strings

sorted_chars = sorted([(char["order"], char["name"]) for char in base_chars])
alphabet = [char for (_, char) in sorted_chars]
sorter = CustomSorter(alphabet, ignorable=ignorables)


# test full workflow

for test_input, expected in sample_data["test_input_to_sort"].items():
    saved = preprocessor(test_input).output_string
    base = presorter(saved).output_string
    custom_order = sorter.word_as_sort_string(base)

    flow = " ==> ".join([test_input, saved, base, custom_order])
    output = custom_order

    print(output == expected, "\t\t", flow)

# TODO: input should have NFC and whitespace stripping applied also

# TODO: build tests from sample data
