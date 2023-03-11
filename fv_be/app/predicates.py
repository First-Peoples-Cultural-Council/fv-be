from rules import predicate


@predicate
def is_publically_viewable_obj(user, obj):
    return obj.state == "published"


@predicate
def is_obj_enabled(user, obj):
    return obj.state == "enabled"


@predicate
def is_obj_new(user, obj):
    return obj.state == "new"


@predicate
def has_enabled_site(user, obj):
    return obj.site.state == "enabled"


@predicate
def has_new_site(user, obj):
    return obj.site.state == "new"


@predicate
def has_publically_viewable_site(user, obj):
    return obj.site.state == "published"


# for use in controlling create/update/delete access for models
def get_role(user, obj):
    membership = user.membership_set.filter(site__id=obj.site.id)
    return str(membership[0].role) if len(membership) > 0 else "guest"


@predicate
def is_at_least_member(user, obj):
    return get_role(user, obj) in ("member", "recorder", "editor", "language_admin")


@predicate
def is_at_least_recorder(user, obj):
    return get_role(user, obj) in ("recorder", "editor", "language_admin")


@predicate
def is_at_least_editor(user, obj):
    return get_role(user, obj) in ("editor", "language_admin")


@predicate
def is_at_least_language_admin(user, obj):
    return get_role(user, obj) in ("language_admin")


@predicate
def is_at_least_staff_admin(user, obj):
    # todo: real implementation
    return user.is_staff


@predicate
def is_superadmin(user, obj):
    # todo: real implementation
    return user.is_superuser


has_member_access_to_obj = is_obj_enabled & is_at_least_member
has_team_access_to_obj = is_obj_new & is_at_least_recorder

has_member_access_to_site = has_enabled_site & is_at_least_member
has_team_access_to_site = has_new_site & is_at_least_recorder

is_visible_object = (
    is_publically_viewable_obj
    | is_superadmin
    | has_member_access_to_obj
    | has_team_access_to_obj
)
has_visible_site = (
    has_publically_viewable_site
    | is_superadmin
    | has_member_access_to_site
    | has_team_access_to_site
)
