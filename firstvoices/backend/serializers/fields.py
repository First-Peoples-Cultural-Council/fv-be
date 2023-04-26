from rest_framework_nested.relations import (
    NestedHyperlinkedIdentityField,
    NestedHyperlinkedRelatedField,
)


class SiteHyperlinkedRelatedField(NestedHyperlinkedRelatedField):
    parent_lookup_kwargs = {"site_slug": "site__slug"}


class SiteHyperlinkedIdentityField(NestedHyperlinkedIdentityField):
    parent_lookup_kwargs = {"site_slug": "site__slug"}
