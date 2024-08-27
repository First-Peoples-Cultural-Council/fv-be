import re

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, Widget

from backend.models import Category, DictionaryEntry

DUMMY_USER_EMAIL = "support@fpcc.ca"


class ChoicesWidget(Widget):
    """Import/export widget to use choice labels instead of internal value.

    Maps display labels to db values for import, and vvsa for export.
    """

    def __init__(self, choices, *args, **kwargs):
        """
        Input:
        - choices: iterable of choices containing (dbvalue, label)
            e.g. [(20, "Public"), ...]
        """
        self.choice_labels = dict(choices)
        self.choice_values = {v: k for k, v in choices}

    def clean(self, value, row=None, *args, **kwargs):
        """Returns the db value given the display value"""
        value = value.strip().lower().title()
        return self.choice_values.get(value) if value else None

    def render(self, value, obj=None):
        """Returns the display value given the db value"""
        return self.choice_labels.get(value)


class ArrayOfStringsWidget(Widget):
    """Import/export widget to split strings on custom separator."""

    def __init__(self, sep: str = ",", *args, **kwargs) -> None:
        super().__init__()
        self.sep = sep

    def clean(self, value: str, row=None, *args, **kwargs) -> list:
        """Converts the display value (string with separator) into array on sep"""
        return [
            string.strip() for string in value.split(sep=self.sep) if string.strip()
        ]

    def render(self, value: list, obj=None) -> str:
        """Converts the db value (array) into a single string for display, using separator"""
        if value:
            return self.sep.join(value)
        return ""


class UserForeignKeyWidget(ForeignKeyWidget):
    """Import/export widget to find/create users from their email.

    If Django cannot find a User with a matching email address, will return dummy user.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(model=get_user_model(), field="email", *args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        """Converts email value from CSV to a User object."""
        user_exists = self.model.objects.filter(email=value).exists()
        if user_exists:
            return super().clean(value, row, **kwargs)
        else:
            dummy_user, _ = self.model.objects.get_or_create(
                **{self.field: DUMMY_USER_EMAIL}, defaults={"email": DUMMY_USER_EMAIL}
            )
            return dummy_user


class InvertedBooleanFieldWidget(Widget):
    """Import/export widget to return expected boolean value for audience related fields."""

    def __init__(self, column, coerce_to_string=True):
        self.column_name = column
        super().__init__(coerce_to_string=coerce_to_string)

    def clean(self, value, row=None, **kwargs):
        cleaned_input = str(value).strip().lower()

        # Returning negative of input value
        if cleaned_input in ["true", "yes", "y", "1"]:
            return False
        elif cleaned_input in ["false", "no", "n", "0"]:
            return True
        else:
            raise ValidationError(
                f"Invalid value in {self.column_name} column. Expected 'true' or 'false'."
            )


class TextListWidget(Widget):
    """Import/export widget to return valid values for arrayFields from attributes
    that can span multiple columns in the input csv."""

    def __init__(self, prefix, *args, **kwargs):
        self.prefix = prefix
        super().__init__(*args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        match_pattern = rf"{self.prefix}[_2-5]*"
        return [
            value
            for key, value in row.items()
            if re.fullmatch(match_pattern, key) and len(value.strip())
        ]


class CategoryWidget(ManyToManyWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(model=Category, field="title", *args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        category_column_name_pattern = r"category[_2-5]*"

        input_categories = {}
        valid_categories = []

        for column, input_value in row.items():
            if re.fullmatch(category_column_name_pattern, column):
                input_categories[column] = input_value.strip()

        # removing empty values from dict
        input_categories = {
            category: value for category, value in input_categories.items() if value
        }

        # If no categories provided, return
        if len(input_categories) == 0:
            return Category.objects.none()

        # Validate categories
        for column, input_value in input_categories.items():
            category_lookup = Category.objects.filter(
                site__id=row["site"], title=input_value
            )
            if len(category_lookup) == 0:
                raise ValidationError(f"Invalid category supplied in column {column}.")
            else:
                valid_categories.append(category_lookup[0])

        return valid_categories


class CleanForeignKeyWidget(ForeignKeyWidget):
    def __init__(self, model, field, title_case=False, *args, **kwargs):
        self.title_case = title_case
        super().__init__(model=model, field=field, *args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        value = value.strip().lower()

        if self.title_case:
            value = value.title()

        return super().clean(value, row, **kwargs)


class RelatedEntriesWidget(ManyToManyWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(model=DictionaryEntry, *args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        column_name_pattern = r"related_entry[_2-5]*"

        input_entries = {}
        valid_entries = []

        for column, input_value in row.items():
            if re.fullmatch(column_name_pattern, column):
                input_entries[column] = input_value.strip()

        # removing empty values from dict
        input_entries = {
            entry: value for entry, value in input_entries.items() if value
        }

        # If no categories provided, return
        if len(input_entries) == 0:
            return Category.objects.none()

        # Validate entries
        for column, input_value in input_entries.items():
            entry_lookup = DictionaryEntry.objects.filter(
                site__id=row["site"], id=input_value
            )
            if len(entry_lookup) == 0:
                raise ValidationError(
                    f"Invalid dictionary entry supplied in column {column}."
                )
            else:
                valid_entries.append(entry_lookup[0])

        return valid_entries
