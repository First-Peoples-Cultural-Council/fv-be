from django.db import models


class TruncatingCharField(models.CharField):
    """
    Custom CharField which auto truncates the value if it goes above the max_length.
    Strips any whitespace in the beginning or in the end before enforcing max length.
    Ref: https://docs.djangoproject.com/en/4.2/ref/models/fields/#django.db.models.Field.get_prep_value
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value:
            return value.strip()[: self.max_length]
        return value


class MimetypeFileFieldMixin:
    def __init__(
        self,
        verbose_name=None,
        name=None,
        mimetype_field=None,
        **kwargs,
    ):
        self.mimetype_field = mimetype_field
        super().__init__(verbose_name, name, **kwargs)

    def check(self, **kwargs):
        # todo: check magic is installed
        return [
            *super().check(**kwargs),
            *self._check_image_library_installed(),
        ]

    def deconstruct(self):
        # todo
        name, path, args, kwargs = super().deconstruct()
        if self.width_field:
            kwargs["width_field"] = self.width_field
        if self.height_field:
            kwargs["height_field"] = self.height_field
        return name, path, args, kwargs
