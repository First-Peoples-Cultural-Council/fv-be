from rules import predicate

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
