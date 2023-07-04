from . import base

#
# reusable view permission filters
#


# NOTE: If this view filter or the predicates that form it are changed
# the search view filter MUST also be changed to match the new logic.
# The view filter can be found at firstvoices/apps/fv_search/permissions.py
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
