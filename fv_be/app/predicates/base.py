from rules import predicate

from fv_be.app.models.constants import Role, Visibility

from .utils import get_role

#
# visibility-based test_predicates
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
def has_public_site(user, obj):
    return obj.site.visibility == Visibility.PUBLIC


@predicate
def has_members_site(user, obj):
    return obj.site.visibility == Visibility.MEMBERS


@predicate
def has_team_site(user, obj):
    return obj.site.visibility == Visibility.TEAM


@predicate
def is_own_obj(user, obj):
    """
    Will only work for models that have a "user" field, mainly Memberships.
    """
    return user.id == obj.user.id


#
# role-based test_predicates
#


@predicate
def is_at_least_member(user, obj):
    return get_role(user, obj) >= Role.MEMBER


@predicate
def is_at_least_assistant(user, obj):
    return get_role(user, obj) >= Role.ASSISTANT


@predicate
def is_at_least_editor(user, obj):
    return get_role(user, obj) >= Role.EDITOR


@predicate
def is_at_least_language_admin(user, obj):
    return get_role(user, obj) >= Role.LANGUAGE_ADMIN


@predicate
def is_at_least_staff_admin(user, obj):
    # todo: real implementation FW-4178
    return user.is_staff or user.is_superuser


@predicate
def is_superadmin(user, obj):
    # todo: real implementation FW-4178
    return user.is_superuser


#
# access-based test_predicates
#
has_public_access_to_obj = is_public_obj & has_public_site
has_member_access_to_obj = (
    is_at_least_member & ~is_team_obj & ~has_team_site
)  # noqa E1130
has_team_access_to_obj = is_at_least_assistant

has_public_access_to_site = has_public_site  # just a convenient alias
has_member_access_to_site = is_at_least_member & ~has_team_site  # noqa E1130
has_team_access_to_site = is_at_least_assistant
