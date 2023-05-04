from rules import predicate

from . import base

#
# reusable view permission test_predicates
#

is_visible_object = predicate(
    lambda: (
        base.has_public_access_to_obj
        | base.is_at_least_staff_admin
        | base.has_member_access_to_obj
        | base.has_team_access_to_obj
    ),
    name="is_visible_object",
)

has_visible_site = predicate(
    lambda: (
        base.has_public_access_to_site
        | base.is_at_least_staff_admin
        | base.has_member_access_to_site
        | base.has_team_access_to_site
    ),
    name="has_visible_site",
)
