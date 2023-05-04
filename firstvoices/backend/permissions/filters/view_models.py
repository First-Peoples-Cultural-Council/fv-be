from . import base

#
# model-specific view permission filters
#


# Site model is visible to all unless it has Team-only visibility
def can_view_site_model(user):
    return (
        base.is_public_obj(user)
        | base.is_members_obj(user)
        | base.is_at_least_staff_admin(user)
        | base.has_team_access_to_obj(user)
    )


# Membership model is visible to admins, and relevant user
def can_view_membership_model(user):
    return (
        base.is_at_least_staff_admin(user)
        | base.is_at_least_language_admin(user)
        | base.is_own_obj(user)
    )
