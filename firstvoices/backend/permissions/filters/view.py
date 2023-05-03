from . import base

#
# reusable view permission test_predicates
#


def is_visible_object(user):
    return (
        base.has_public_access_to_obj(user)
        | base.is_at_least_staff_admin(user)
        | base.has_member_access_to_obj(user)
        | base.has_team_access_to_obj(user)
    )


def has_visible_site(user):
    return (
        base.has_public_access_to_site(user)
        | base.is_at_least_staff_admin(user)
        | base.has_member_access_to_site(user)
        | base.has_team_access_to_site(user)
    )
