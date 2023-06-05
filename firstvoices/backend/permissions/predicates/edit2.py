from rules import predicate

from . import base


@predicate
def can_add_core_language_data(user, obj):
    """
    Same as ``can_edit_core_language_data`` but does not check the visibility of the object that is saved in the db.

    - Assistant has permission for Team-visibility data
    - Editor, Language Admin, and Superadmin have permission
    """
    return (
        base.has_at_least_editor_membership(user, obj)
        | base.is_superadmin(user, obj)
        | (
            base.has_at_least_assistant_membership(user, obj)
            & base.is_team_obj(user, obj)
        )
    )


@predicate
def can_edit_core_language_data(user, obj):
    """
    Same as ``can_add_core_language_data`` but also checks the visibility of the object that is saved in the db.

    - Assistant has permission for Team-visibility data
    - Editor, Language Admin, and Superadmin have permission
    """
    return (
        base.has_at_least_editor_membership(user, obj)
        | base.is_superadmin(user, obj)
        | (
            base.has_at_least_assistant_membership(user, obj)
            & base.is_team_obj(user, obj)
            & base.is_saved_team_obj(user, obj)
        )
    )
