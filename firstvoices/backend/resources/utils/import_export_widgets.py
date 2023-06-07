from import_export.widgets import ForeignKeyWidget, Widget

from backend.models.user import User


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
    """Import/export widget to find users by their email, and create in django if missing."""

    def __init__(self, create=False, *args, **kwargs):
        self.create = create
        super().__init__(model=User, field="email", *args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        if self.create:
            user, _ = self.model.objects.get_or_create(
                **{self.field: value}, defaults={"id": value}
            )
            return user
        else:
            return super().clean(value, row, **kwargs)
