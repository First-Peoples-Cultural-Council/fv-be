from fv_be.app.predicates import base

#
# model-specific view permission test_predicates
#

# Site model is visible to all unless it has Team-only visibility
can_view_site_model = (
    base.is_public_obj
    | base.is_members_obj
    | base.is_at_least_staff_admin
    | base.has_team_access_to_obj
)

# Membership model is visible to admins, and relevant user
can_view_membership_model = (
    base.is_at_least_staff_admin | base.is_at_least_language_admin | base.is_own_obj
)
