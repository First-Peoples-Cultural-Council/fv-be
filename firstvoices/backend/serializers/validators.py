from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator, qs_filter

from backend.serializers.serializer_utils import get_site_from_context


class SameSite:
    """
    Validates that the value has the same site as the requested URL.
    """

    message = _("Must be in the same site.")
    requires_context = True

    def __init__(self, queryset, message=None):
        self.queryset = queryset
        self.message = message or self.message

    def __call__(self, value, serializer):
        expected_site_slug = get_site_from_context(serializer)
        if value.site.slug != expected_site_slug:
            raise serializers.ValidationError(self.message)


class HasNoParent:
    """
    Validates that the value does not have a parent.
    """

    message = _("Must not have a parent.")

    def __init__(self, queryset, message=None):
        self.queryset = queryset
        self.message = message or self.message

    def __call__(self, value):
        if value.parent:
            raise serializers.ValidationError(self.message)


class UniqueForSite(UniqueValidator):
    message = _("This field must be unique within the site.")
    site_slug = None

    def filter_queryset(self, value, queryset, field_name):
        """
        Filter the queryset to all instances matching the given attribute.
        """
        filter_kwargs = {f"{field_name}__{self.lookup}": value}
        filter_kwargs["site__slug"] = self.site_slug
        return qs_filter(queryset, **filter_kwargs)

    def __call__(self, value, serializer_field):
        self.site_slug = get_site_from_context(serializer_field)
        super().__call__(value, serializer_field)
