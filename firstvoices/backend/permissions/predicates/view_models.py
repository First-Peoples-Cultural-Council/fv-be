from rules import Predicate

from . import base, view

#
# model-specific view permission predicates
#

# Rule for who can see detailed site info including homepage, content APIs, etc
can_view_site = Predicate(
    (base.is_at_least_staff_admin | base.has_team_access)
    | (
        (base.has_member_access_to_site_obj | base.is_public_obj) & ~base.is_hidden_site
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


# Can view immersion label, if the related dictionary-entry should be public
can_view_immersion_label = Predicate(
    (
        base.has_public_access_to_related_dictionary_entry
        | base.has_member_access_to_related_dictionary_entry
        | base.is_at_least_staff_admin
        | base.has_team_access
    ),
    name="can_view_immersion_label",
)
