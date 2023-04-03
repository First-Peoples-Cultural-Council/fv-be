import os
import re
import unicodedata

# import g2p, will be used in fw-4172
import pandas as pd
import yaml

from ..models.characters import Character, CharacterVariant
from ..models.sites import Site


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


def nfc(string: str) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFC", string))


def generate_confusable_map(filepath: str) -> dict:
    """Generates the confusable map from a provided confusables file."""
    # TODO: This is temporary to get confusables working,
    #  ideally we will store confusables either in the database or in site-specific files.
    #  Maybe we should return to the idea of a confusable model, and pass the confusables like characters/variants?

    df = pd.read_csv(filepath)

    # remove unused columns
    df = df.drop(["id", "confusable_unicode"], axis=1)

    # remove rows with null confusable_char values
    df = df.dropna(subset=["confusable_char"])

    # group the confusable characters by their label
    groups = df.groupby("label")["confusable_char"].apply(
        lambda x: [s.split(",") for s in x]
    )

    # flatten the list of lists
    groups = groups.apply(lambda x: [item for sublist in x for item in sublist])

    # convert the groups into a dictionary
    confusables_dict = groups.to_dict()

    return confusables_dict


class CharacterMappingFileGenerator:
    """Generates the appropriate site mapping files for a given language."""

    def __init__(self):
        self.default_yaml_location = "characterfiles_temp/default_config.yaml"
        self.confusables_location = "characterfiles_temp/all_characters_confusables.csv"

    def generate_preprocess_csv(
        self,
        base_chars: list[Character],
        variants: list[CharacterVariant],
        site_config: str,
    ):
        """Generates the confusable to canonical g2p mapping csv file."""

        base_character_info = [
            {"title": char.title, "order": char.sort_order} for char in base_chars
        ]
        variant_character_map = {}

        variant_character_map.update(
            {variant.title: variant.base_character.title} for variant in variants
        )

        variant_character_map.update(
            {char["title"]: char["title"] for char in base_character_info}
        )
        # TODO: Temporary, see generate_confusable_map comments
        confusables = generate_confusable_map(self.confusables_location)

        # TODO: Logging rather than print statements
        confusables_map = {}
        for variant, confusable_options in confusables.items():
            for confusable in {nfc(c) for c in confusable_options}:
                if confusable in variant_character_map:
                    print("Skipping confusable {} -- same as a canonical character")
                elif confusable in confusables_map:
                    # FIXME: needs more tweaking, e.g. what if same confusable used 3 times
                    print("Skipping confusable {} -- listed for multiple characters")
                    del confusables_map[confusable]
                else:
                    confusables_map[confusable] = variant
                    print(f"Adding confusable {confusable} for {variant}")

        # Make dataframe and save to csv
        preprocessor_map = pd.DataFrame(
            [
                {"in": confusable, "out": canonical}
                for confusable, canonical in confusables_map.items()
            ]
        )

        # Find preprocess settings
        for mapping in site_config["mappings"]:
            if mapping["in_lang"].endswith("-input"):
                preprocess_settings = mapping
            else:
                # Error handling
                print("No appropriate mapping found in site config")

        csv_path = os.path.join("/characterfiles_temp", preprocess_settings["mapping"])

        preprocessor_map.to_csv(csv_path, index=False, header=False)

        return csv_path

    def generate_presort_csv(
        self,
        base_chars: list[Character],
        variants: list[CharacterVariant],
        site_config: str,
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

        presorter_map = pd.DataFrame(
            [
                {"in": variant, "out": base}
                for variant, base in variant_character_map.items()
            ]
        )

        # Find presort settings
        for mapping in site_config["mappings"]:
            if mapping["out_lang"].endswith("-base"):
                presort_settings = mapping
            else:
                # Error handling
                print("No appropriate mapping found in site config")

        csv_path = os.path.join("/characterfiles_temp", presort_settings["mapping"])

        presorter_map.to_csv(csv_path, index=False, header=False)

        return csv_path

    def get_site_yaml_config(self, site: Site) -> str:
        """Generates the site-specific yaml config file using a yaml template."""

        site_name = f"FV {site.title}"
        site_code = f"fv-{site.slug}"

        with open(os.path.join(self.default_yaml_location)) as f:
            default_config = f.read()

        site_config = default_config.format(language=site_name, code=site_code)
        site_config = yaml.safe_load(site_config)

        return site_config
