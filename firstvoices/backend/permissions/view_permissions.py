import rules
from filters import is_superadmin

rules.add_perm("has_superadmin_access", is_superadmin)
