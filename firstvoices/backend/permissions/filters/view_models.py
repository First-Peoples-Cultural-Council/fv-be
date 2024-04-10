from . import base, view

#
# model-specific view permission filters
#


# Rule for who can see detailed site info including homepage, content APIs, etc
def can_view_site(user):
    return (
        base.is_at_least_staff_admin(user)
        | base.has_team_access_to_site_obj(user)
        | base.has_member_access_to_site_obj(user) & ~base.is_hidden_site()
        | base.is_public_obj() & ~base.is_hidden_site()
    )


# Membership model is visible to admins, and relevant user
def can_view_membership_model(user):
    return (
        base.is_at_least_staff_admin(user)
        | base.has_language_admin_membership(user)
        | (base.is_own_obj(user) & view.has_visible_site(user))
    )


# user can view an immersion label, if the user can view the related dictionary entry
def can_view_immersion_label(user):
    return (
        base.has_public_access_to_related_dictionary_entry(user)
        | base.has_member_access_to_related_dictionary_entry(user)
        | base.is_at_least_staff_admin(user)
        | base.has_team_access_to_obj(user)
    )
