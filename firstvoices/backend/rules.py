import rules

from backend.permissions.predicates.base import is_superadmin

rules.add_perm("views.has_custom_order_access", is_superadmin)
