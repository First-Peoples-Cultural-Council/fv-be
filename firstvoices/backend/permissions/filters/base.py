from django.db.models import F, Q

from backend.models.constants import AppRole, Role, Visibility
from backend.permissions.utils import get_app_role


#
# site-based filter
#
def has_site(site):
    return Q(site=site)


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
# role-based test_predicates
#


def get_site_role_at_least_filter(user, role):
    return Q(site__membership_set__user=user) & Q(site__membership_set__role__gte=role)


def is_at_least_member(user):
    return get_site_role_at_least_filter(user, Role.MEMBER)


def is_at_least_assistant(user):
    return get_site_role_at_least_filter(user, Role.ASSISTANT)


def is_at_least_editor(user):
    return get_site_role_at_least_filter(user, Role.EDITOR)


def is_at_least_language_admin(user):
    return get_site_role_at_least_filter(user, Role.LANGUAGE_ADMIN)


#
# App Role filters
#
def get_app_role_filter(user, app_role):
    if get_app_role(user) >= app_role:
        return Q(id=F("id"))  # always true
    else:
        return ~Q(id=F("id"))  # always false


def is_at_least_staff_admin(user):
    return get_app_role_filter(user, AppRole.STAFF)


def is_superadmin(user, obj):
    return get_app_role_filter(user, AppRole.SUPERADMIN)


#
# access-based filters
#
def has_public_access_to_obj(user):
    return is_public_obj() & has_public_site()


def has_member_access_to_obj(user):
    return is_at_least_member(user) & ~is_team_obj() & ~has_team_site()


def has_team_access_to_obj(user):
    return is_at_least_assistant(user)


def has_public_access_to_site(user):
    return has_public_site()  # just a convenient alias


def has_member_access_to_site(user):
    return is_at_least_member(user) & ~has_team_site()


def has_team_access_to_site(user):
    return is_at_least_assistant(user)
