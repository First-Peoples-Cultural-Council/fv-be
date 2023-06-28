from django.contrib.auth import get_user_model
from import_export.widgets import ForeignKeyWidget, Widget


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

    When Django cannot find a User with a matching email address,
    it will create a new one if create=True, otherwise, will return dummy user.
    """

    def __init__(self, create=False, *args, **kwargs):
        self.create = create
        super().__init__(model=get_user_model(), field="email", *args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        """Converts email value from CSV to a User object."""

        user_exists = self.model.objects.filter(email=value).count() == 1
        if user_exists:
            return super().clean(value, row, **kwargs)
        elif self.create:
            # steps missing here to actually migrate/match users
            user, _ = self.model.objects.get_or_create(
                **{self.field: value}, defaults={"id": value}
            )
            return user
        else:
            # for now, return a dummy user
            dummy_user, _ = self.model.objects.get_or_create(
                **{self.field: "test@test.com"}, defaults={"id": "test@test.com"}
            )
            return dummy_user
