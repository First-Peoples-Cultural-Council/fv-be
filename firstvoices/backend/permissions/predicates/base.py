from rules import Predicate, predicate

from backend.models.constants import AppRole, Role, Visibility
from backend.permissions.utils import get_app_role, get_site_role


#
# visibility-based predicates
#
@predicate
def is_public_obj(user, obj):
    return obj.visibility == Visibility.PUBLIC


@predicate
def is_members_obj(user, obj):
    return obj.visibility == Visibility.MEMBERS


@predicate
def is_team_obj(user, obj):
    return obj.visibility == Visibility.TEAM


@predicate
def is_saved_team_obj(user, obj):
    """
    Checks the visibility of the saved version of the given obj, not the version in memory.
    """
    saved = type(obj).objects.filter(pk=obj.pk).first()
    return saved.visibility == Visibility.TEAM


@predicate
def has_public_site(user, obj):
    return obj.site.visibility == Visibility.PUBLIC


@predicate
def has_members_site(user, obj):
    return obj.site.visibility == Visibility.MEMBERS


@predicate
def has_team_site(user, obj):
    return obj.site.visibility == Visibility.TEAM


@predicate
def has_saved_team_site(user, obj):
    """
    Checks the site visibility of the saved version of the given obj, not the version in memory.
    """
    saved = type(obj).objects.filter(pk=obj.pk).first()
    return saved.site.visibility == Visibility.TEAM


@predicate
def is_own_obj(user, obj):
    """
    Will only work for models that have a "user" field, mainly Memberships.
    """
    return user.id == obj.user.id


#
# role-based predicates
#


@predicate
def has_at_least_member_membership(user, obj):
    return get_site_role(user, obj) >= Role.MEMBER


@predicate
def has_at_least_assistant_membership(user, obj):
    return get_site_role(user, obj) >= Role.ASSISTANT


@predicate
def has_at_least_editor_membership(user, obj):
    return get_site_role(user, obj) >= Role.EDITOR


@predicate
def has_language_admin_membership(user, obj):
    return get_site_role(user, obj) >= Role.LANGUAGE_ADMIN


@predicate
def is_at_least_staff_admin(user, obj):
    return get_app_role(user) >= AppRole.STAFF


@predicate
def is_superadmin(user, obj):
    return get_app_role(user) == AppRole.SUPERADMIN


@predicate
def is_hidden_obj(user, obj):
    return obj.is_hidden


#
# site and app role combos
is_at_least_language_admin = Predicate(
    has_language_admin_membership | is_at_least_staff_admin,
    name="is_at_least_language_admin",
)

#
# access-based predicates
#
has_public_access_to_obj = Predicate(
    is_public_obj & has_public_site, name="has_public_access_to_obj"
)
has_member_access_to_obj = (
    has_at_least_member_membership & ~is_team_obj & ~has_team_site
)  # noqa E1130
has_team_access = has_at_least_assistant_membership

has_public_access_to_site = has_public_site  # just a convenient alias
has_member_access_to_site = (
    has_at_least_member_membership & ~has_team_site
)  # noqa E1130

has_public_access_to_site_obj = predicate(is_public_obj)
has_member_access_to_site_obj = (
    has_at_least_member_membership & ~is_team_obj
)  # noqa E1130
