from rest_framework_nested.relations import NestedHyperlinkedRelatedField

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
