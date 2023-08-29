from rules import Predicate

from . import base, view

#
# model-specific view permission predicates
#

# Rule for who can see detailed site info including homepage, content APIs, etc
can_view_site = Predicate(
    (
        base.is_public_obj
        | base.is_at_least_staff_admin
        | base.has_member_access_to_site_obj
        | base.has_team_access
    ),
    name="can_view_site",
)

# Membership model is visible to admins, and relevant user
can_view_user_info = Predicate(
    (
        base.is_at_least_staff_admin
        | base.has_language_admin_membership
        | (base.is_own_obj & view.has_visible_site)
    ),
    name="can_view_membership_model",
)
