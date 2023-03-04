from .predicates import *

# Create combined predicates from predicates.py
can_view_published = is_published & is_language_published
can_view_new = is_new & (is_recorder | is_editor | is_language_admin)
can_view_enabled = is_enabled & (is_member | is_recorder | is_editor | is_language_admin)
can_view_disabled = is_new & (is_recorder | is_editor | is_language_admin)
can_view_republish = is_new & (is_recorder | is_editor | is_language_admin)

can_view_model = can_view_published | can_view_new | can_view_enabled | can_view_disabled | can_view_republish | is_super_admin

# Create rules based on the combined predicates
rules.add_rule('can_view_model', can_view_model)