def get_site_id(obj):
    """
    Returns the site id for the object, with handling for Site objects as well as site content models
    """
    return obj.id if obj.__class__.__name__ == "Site" else obj.site.id


def get_site_role(user, obj):
    """
    Returns an integer corresponding to a user's role on the site matching
    the given obj, or -1 if they are not a member of that site.
    """

    if user.is_anonymous:
        return -1

    membership = user.memberships.filter(site__id=get_site_id(obj))
    return membership[0].role if len(membership) > 0 else -1


def get_app_role(user):
    """
    Returns an integer corresponding to a user's app-level role.
    """

    if user.is_anonymous:
        return -1

    return user.app_role.role if hasattr(user, "app_role") else -1


def filter_by_viewable(user, queryset):
    """
    Returns a new queryset containing items from queryset that the user has permission to view
    """
    view_permission_filter = queryset.model.objects.visible_as_filter(user)
    return queryset.filter(view_permission_filter).distinct()
