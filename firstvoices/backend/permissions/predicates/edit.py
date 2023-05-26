from rules import Predicate

from . import base

#
# reusable edit permission predicates
#

is_visible_object = Predicate(
    (
        base.has_public_access_to_obj
        | base.is_at_least_staff_admin
        | base.has_member_access_to_obj
        | base.has_team_access
    ),
    name="is_visible_object",
)
