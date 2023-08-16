from django.contrib.auth import get_user_model
from import_export.widgets import ForeignKeyWidget, Widget

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
        return self.choice_values.get(value) if value else None

    def render(self, value, obj=None):
        """Returns the display value given the db value"""
        return self.choice_labels.get(value)


class UserForeignKeyWidget(ForeignKeyWidget):
    """Import/export widget to find/create users from their email.

    If Django cannot find a User with a matching email address, will return dummy user.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(model=get_user_model(), field="email", *args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        """Converts email value from CSV to a User object."""
        if not value:
            # leave field empty if no email provided
            return None

        user_exists = self.model.objects.filter(email=value).count() == 1
        if user_exists:
            return super().clean(value, row, **kwargs)
        else:
            dummy_user, _ = self.model.objects.get_or_create(
                **{self.field: DUMMY_USER_EMAIL}, defaults={"email": DUMMY_USER_EMAIL}
            )
            return dummy_user
