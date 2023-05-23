from rest_framework_nested.relations import NestedHyperlinkedRelatedField


class SiteHyperlinkedRelatedField(NestedHyperlinkedRelatedField):
    """
    Supports nested URLs. Will use the view kwarg values named in parent_lookup_kwargs as literal
    values when reversing the URL, to eliminate extra database queries. This means this will only work within
    views that have the same nested structure as the target URL (links to objects in the same site). For use in other
    contexts, see NestedHyperlinkedRelatedField, which uses model attribute lookups instead of url kwarg lookups.
    """

    parent_lookup_kwargs = {"site_slug": "site_slug"}

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

        # all levels will be treated as site values, so this is effectively a single-level lookup
        for parent_lookup_kwarg in list(self.parent_lookup_kwargs.keys()):
            underscored_lookup = self.parent_lookup_kwargs[parent_lookup_kwarg]

            try:
                # use the Django ORM to lookup this value, e.g., obj.parent.pk
                lookup_value = request.parser_context["kwargs"][underscored_lookup]
            except AttributeError:
                # Not nested. Act like a standard HyperlinkedRelatedField
                return super().get_url(obj, view_name, request, format)

            # store the lookup_name and value in kwargs, which is later passed to the reverse method
            kwargs.update({parent_lookup_kwarg: lookup_value})

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class SiteHyperlinkedIdentityField(SiteHyperlinkedRelatedField):
    """
    Supports nested URLs. Will use the view kwarg values named in parent_lookup_kwargs as literal
    values when reversing the URL, to eliminate extra database queries. This means this will only work within
    views that have the same nested structure as the target URL. For use in other contexts, see
    NestedHyperlinkedIdentityField.
    """

    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, "The `view_name` argument is required."
        kwargs["read_only"] = True
        kwargs["source"] = "*"
        super().__init__(view_name=view_name, **kwargs)
