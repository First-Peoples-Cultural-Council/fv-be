from . import base

#
# reusable view permission test_predicates
#

is_visible_object = (
    base.has_public_access_to_obj
    | base.is_at_least_staff_admin
    | base.has_member_access_to_obj
    | base.has_team_access_to_obj
)
has_visible_site = (
    base.has_public_access_to_site
    | base.is_at_least_staff_admin
    | base.has_member_access_to_site
    | base.has_team_access_to_site
)
