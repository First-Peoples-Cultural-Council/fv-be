from rules import predicate

from . import base
from .base import (
    has_at_least_assistant_membership,
    has_at_least_editor_membership,
    has_language_admin_membership,
    is_superadmin,
)

#
# role-based predicates for edit permissions
#

is_at_least_assistant_or_super = predicate(
    has_at_least_assistant_membership | is_superadmin,
    name="is_at_least_assistant_or_super",
)
is_at_least_editor_or_super = predicate(
    has_at_least_editor_membership | is_superadmin, name="is_at_least_editor_or_super"
)
is_language_admin_or_super = predicate(
    has_language_admin_membership | is_superadmin,
    name="is_at_least_language_admin_or_super",
)


@predicate
def can_add_core_uncontrolled_data(user, obj):
    """
    Same as ``can_edit_core_uncontrolled_data`` but does not check the visibility of the object that is saved in the db.

    - Assistant has permission for Team-visibility data
    - Editor, Language Admin, and Superadmin have permission
    """
    return (
        base.has_at_least_editor_membership(user, obj)
        | base.is_superadmin(user, obj)
        | (
            base.has_at_least_assistant_membership(user, obj)
            & base.is_team_obj(user, obj)  # will be called with a site object
        )
    )


@predicate
def can_edit_core_uncontrolled_data(user, obj):
    """
    Same as ``can_add_core_uncontrolled_data`` but also checks the visibility of the object that is saved in the db.

    - Assistant has permission for Team-visibility data
    - Editor, Language Admin, and Superadmin have permission
    """
    return (
        base.has_at_least_editor_membership(user, obj)
        | base.is_superadmin(user, obj)
        | (
            base.has_at_least_assistant_membership(user, obj)
            & base.has_team_site(user, obj)
            & base.has_saved_team_site(user, obj)
        )
    )
