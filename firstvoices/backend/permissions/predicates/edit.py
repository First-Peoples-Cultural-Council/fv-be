from rules import predicate, is_staff

from . import base
from .base import (
    has_at_least_assistant_membership,
    has_at_least_editor_membership,
    has_language_admin_membership,
    is_superadmin,
    is_at_least_staff_admin
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
is_at_least_language_admin = predicate(
    has_language_admin_membership | is_at_least_staff_admin,
    name="is_at_least_language_admin",
)

"""
Same as ``can_edit_core_uncontrolled_data`` but does not check the visibility of the object that is saved in the db.

- Assistant has permission for Team-visibility data
- Editor, Language Admin, and Superadmin have permission
"""
can_add_core_uncontrolled_data = predicate(
    base.has_at_least_editor_membership
    | base.is_superadmin
    | (
        base.has_at_least_assistant_membership
        & base.is_team_obj  # will be called with a site object
    ),
    name="can_add_core_uncontrolled_data",
)


"""
Same as ``can_add_core_uncontrolled_data`` but also checks the visibility of the object that is saved in the db.

- Assistant has permission for Team-visibility data
- Editor, Language Admin, and Superadmin have permission
"""
can_edit_core_uncontrolled_data = predicate(
    base.has_at_least_editor_membership
    | base.is_superadmin
    | (
        base.has_at_least_assistant_membership
        & base.has_team_site
        & base.has_saved_team_site
    ),
    name="can_edit_core_uncontrolled_data",
)

# just a convenient alias
can_delete_core_uncontrolled_data = predicate(
    is_at_least_editor_or_super, name="can_edit_core_uncontrolled_data"
)

# This predicate must be combined with the CreateControlledSiteContentSerializerMixin in
# backend/serializers/base_serializers.py
can_add_controlled_data = predicate(
    is_at_least_assistant_or_super,
    name="can_add_controlled_data",
)

can_edit_controlled_data = predicate(
    base.has_at_least_editor_membership
    | base.is_superadmin
    | (
        base.has_at_least_assistant_membership
        & base.is_team_obj
        & base.is_saved_team_obj
    ),
    name="can_edit_controlled_data",
)

# another convenient alias
can_delete_controlled_data = predicate(
    is_at_least_editor_or_super, name="can_delete_controlled_data"
)
