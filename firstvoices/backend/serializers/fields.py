from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from backend.models.constants import Visibility
from backend.serializers.utils import get_site_from_context


class SiteHyperlinkedRelatedField(NestedHyperlinkedRelatedField):
    """
    Supports nested URLs. Will use the site provided in the serializer context when reversing the URL, to eliminate
    extra database queries. This means this will only work within views that have the same nested url structure as the
    target URL (links to objects in the same site). For use in other contexts, see NestedHyperlinkedRelatedField,
    which uses model attribute lookups instead of url kwarg lookups.
    """

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, "pk") and obj.pk in (None, ""):
            return None

        # default lookup from rest_framework.relations.HyperlinkedRelatedField
        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_url_kwarg: lookup_value}

        # add the site lookup
        kwargs.update({"site_slug": get_site_from_context(self).slug})

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class SiteHyperlinkedIdentityField(SiteHyperlinkedRelatedField):
    """
    Supports nested URLs. Will use the site provided in the serializer context when reversing the URL, to eliminate
    extra database queries. This means this will only work within views that have the same nested url structure as the
    target URL (links to objects in the same site). For use in other contexts, see NestedHyperlinkedRelatedField,
    which uses model attribute lookups instead of url kwarg lookups.
    """

    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, "The `view_name` argument is required."
        kwargs["read_only"] = True
        kwargs["source"] = "*"
        super().__init__(view_name=view_name, **kwargs)


class SiteViewLinkField(serializers.Field):
    """
    Read-only field that returns a url to a site content view for the
    view_name, and the site in context. Only works for site serializers.
    """

    def __init__(self, view_name, **kwargs):
        self.view_name = view_name
        kwargs["source"] = "*"
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)

    def to_representation(self, value):
        site = self.parent.instance
        return reverse(
            self.view_name,
            args=[site.slug],
            request=self.context["request"],
        )


class WritableVisibilityField(serializers.CharField):
    def to_internal_value(self, data):
        try:
            return Visibility[data.upper()]
        except KeyError:
            raise serializers.ValidationError("Invalid visibility option.")

    def to_representation(self, value):
        visibility_map = {choice[0]: choice[1] for choice in Visibility.choices}
        try:
            return visibility_map[value].lower()
        except KeyError:
            raise serializers.ValidationError("Invalid visibility value.")


class NullableCharField(serializers.CharField):
    def validate_empty_values(self, data):
        if data is None:
            data = ""
        return super().validate_empty_values(data)


class EnumField(serializers.Field):
    enum = None

    def __init__(self, enum, *args, **kwargs):
        self.enum = enum
        return super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        return self.enum(obj).label

    def to_internal_value(self, data):
        return self.enum[data.upper()]
