from .base import (
    has_at_least_assistant_membership,
    has_at_least_editor_membership,
    has_language_admin_membership,
    is_superadmin,
)

#
# role-based predicates, mainly for edit permissions
#


def is_at_least_assistant_or_super(user):
    return has_at_least_assistant_membership(user) | is_superadmin(user)


def is_at_least_editor_or_super(user):
    return has_at_least_editor_membership(user) | is_superadmin(user)


def is_language_admin_or_super(user):
    return has_language_admin_membership(user) | is_superadmin(user)
