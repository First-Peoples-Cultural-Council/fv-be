from django.db.models import F, Q

from backend.models.constants import AppRole, Role, Visibility
from backend.permissions.utils import get_app_role


#
# equivalents for built-in predicates
#
def always_allow(user=None):
    return Q(id=F("id"))


def always_deny(user=None):
    return ~Q(id=F("id"))


def always_true(user=None):
    return always_allow()


def always_false(user=None):
    return always_deny()


#
# site-based filter
#
def has_site(site):
    return Q(site=site)


#
# user-based filter
#
def is_own_obj(user):
    """
    Will only work for models that have a "user" field, mainly Memberships.
    """
    if user.is_anonymous:
        return always_false(user)

    return Q(user=user)


#
# visibility-based filters
#
def get_obj_visibility_query(visibility):
    return Q(visibility=visibility)


def is_public_obj():
    return get_obj_visibility_query(Visibility.PUBLIC)


def is_members_obj():
    return get_obj_visibility_query(Visibility.MEMBERS)


def is_team_obj():
    return get_obj_visibility_query(Visibility.TEAM)


def get_site_visibility_query(visibility):
    return Q(site__visibility=visibility)


def has_public_site():
    return get_site_visibility_query(Visibility.PUBLIC)


def has_members_site():
    return get_site_visibility_query(Visibility.MEMBERS)


def has_team_site():
    return get_site_visibility_query(Visibility.TEAM)


#
# role-based filters
#
def get_site_role_at_least_filter(user, role):
    if user.is_anonymous:
        return always_false(user)

    return Q(site__membership_set__user=user) & Q(site__membership_set__role__gte=role)


def has_at_least_member_membership(user):
    return get_site_role_at_least_filter(user, Role.MEMBER)


def has_at_least_assistant_membership(user):
    return get_site_role_at_least_filter(user, Role.ASSISTANT)


def has_at_least_editor_membership(user):
    return get_site_role_at_least_filter(user, Role.EDITOR)


def has_language_admin_membership(user):
    return get_site_role_at_least_filter(user, Role.LANGUAGE_ADMIN)


#
# model attribute-based predicates
#
def is_hidden_site():
    return Q(is_hidden=True)


#
# App Role filters
#
def get_app_role_filter(user, app_role):
    if get_app_role(user) >= app_role:
        return always_true()
    else:
        return always_false()


def is_at_least_staff_admin(user):
    return get_app_role_filter(user, AppRole.STAFF)


def is_superadmin(user):
    return get_app_role_filter(user, AppRole.SUPERADMIN)


#
# combo site-and-app role filters
#
def is_at_least_language_admin(user):
    return has_language_admin_membership(user) | is_at_least_staff_admin(user)


#
# access-based filters
#
def has_public_access_to_obj(user=None):
    return is_public_obj() & has_public_site()


def has_member_access_to_obj(user):
    return has_at_least_member_membership(user) & ~is_team_obj() & ~has_team_site()


def has_team_access_to_obj(user):
    return has_at_least_assistant_membership(user)


def has_public_access_to_site(user=None):
    return has_public_site()  # just a convenient alias


def has_member_access_to_site(user):
    return has_at_least_member_membership(user) & ~has_team_site()


def has_team_access_to_site(user):
    return has_at_least_assistant_membership(user)


def has_member_access_to_site_obj(user):
    """Special case for getting the membership directly from a site model object"""
    if user.is_anonymous:
        return always_false(user)

    return Q(membership_set__user=user) & Q(membership_set__role__gte=Role.MEMBER)


def has_team_access_to_site_obj(user):
    """Special case for getting the membership directly from a site model object"""
    if user.is_anonymous:
        return always_false(user)

    return Q(membership_set__user=user) & Q(membership_set__role__gte=Role.ASSISTANT)


#
# Filters for related dictionary entry
# used in ImmersionLabel
def has_member_access_to_related_dictionary_entry(user):
    return (
        has_at_least_member_membership(user)
        & ~Q(dictionary_entry__visibility=Visibility.TEAM)
        & ~has_team_site()
    )


# Adding NOSONAR to prevent sonar from raising warnings for unused parameter
def has_public_access_to_related_dictionary_entry(user=None):  # NOSONAR
    return Q(dictionary_entry__visibility=Visibility.PUBLIC) & Q(
        site__visibility=Visibility.PUBLIC
    )
