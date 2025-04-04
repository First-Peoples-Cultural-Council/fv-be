from rules import Predicate

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

is_at_least_assistant_or_super = Predicate(
    has_at_least_assistant_membership | is_superadmin,
    name="is_at_least_assistant_or_super",
)
is_at_least_editor_or_super = Predicate(
    has_at_least_editor_membership | is_superadmin, name="is_at_least_editor_or_super"
)
is_language_admin_or_super = Predicate(
    has_language_admin_membership | is_superadmin,
    name="is_language_admin_or_super",
)


"""
- Assistant has permission for Team-visibility data
- Editor, Language Admin, and Superadmin have permission
"""
can_delete_media = Predicate(
    base.has_at_least_editor_membership
    | base.is_superadmin
    | (
        base.has_at_least_assistant_membership
        & base.has_team_site
        & base.has_saved_team_site
    ),
    name="can_edit_core_uncontrolled_data",
)

# This predicate must be combined with the ValidateAssistantWritePermissionMixin in
# backend/serializers/base_serializers.py
can_add_controlled_data = Predicate(
    is_at_least_assistant_or_super,
    name="can_add_controlled_data",
)

can_edit_controlled_data = Predicate(
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
can_delete_controlled_data = Predicate(
    is_at_least_editor_or_super, name="can_delete_controlled_data"
)
